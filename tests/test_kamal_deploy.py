from pathlib import Path

RECIPE_PATH = Path("config/deploy.yml")
SECRETS_FIXTURE = Path("tests/fixtures/kamal/secrets")
HOST_ADDRESS = "138.201.118.229"
PUBLIC_SITE_NAMES = ("image.bondev.eu", "www.image.bondev.eu")
IMAGE_NAME = "shved270189/image_compressor"
REGISTRY_USERNAME = "shved270189"
SERVICE_NAME = "image_compressor"
IMAGE_ARCHITECTURE = "amd64"
LISTENING_PORT = 8000
HEALTH_CHECK_PATH = "/api/health"
REGISTRY_PASSWORD_NAME = "KAMAL_REGISTRY_PASSWORD"


def load_simple_yaml(text):
    items = []
    for raw in text.splitlines():
        stripped = raw.split(" #", 1)[0].rstrip()
        if not stripped.strip() or stripped.lstrip().startswith("#"):
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        items.append((indent, stripped.strip()))
    value, _ = _parse_yaml(items, 0, 0)
    return value if value is not None else {}


def _parse_scalar(text):
    if text in {"true", "True", "yes"}:
        return True
    if text in {"false", "False", "no"}:
        return False
    if text in {"null", "~"}:
        return None
    if text.isdigit() or (text.startswith("-") and text[1:].isdigit()):
        return int(text)
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1]
    return text


def _parse_yaml(items, index, min_indent):
    if index >= len(items):
        return None, index
    indent, content = items[index]
    if indent < min_indent:
        return None, index
    if content.startswith("- "):
        return _parse_yaml_list(items, index, indent)
    return _parse_yaml_map(items, index, indent)


def _parse_yaml_list(items, index, indent):
    sequence = []
    while index < len(items):
        item_indent, content = items[index]
        if item_indent != indent or not content.startswith("- "):
            break
        rest = content[2:].strip()
        index += 1
        if rest.endswith(":") and not rest.startswith("- "):
            key = rest[:-1].strip()
            if index < len(items) and items[index][0] > indent:
                child, index = _parse_yaml(items, index, items[index][0])
            else:
                child = None
            sequence.append({key: child})
        elif rest:
            sequence.append(_parse_scalar(rest))
        elif index < len(items) and items[index][0] > indent:
            child, index = _parse_yaml(items, index, items[index][0])
            sequence.append(child)
        else:
            sequence.append(None)
    return sequence, index


def _parse_yaml_map(items, index, indent):
    mapping = {}
    while index < len(items):
        item_indent, content = items[index]
        if item_indent < indent or content.startswith("- "):
            break
        if item_indent != indent:
            break
        key, separator, value = content.partition(":")
        if not separator:
            break
        index += 1
        value = value.strip()
        if value:
            mapping[key.strip()] = _parse_scalar(value)
        elif index < len(items) and items[index][0] > indent:
            child, index = _parse_yaml(items, index, items[index][0])
            mapping[key.strip()] = child
        else:
            mapping[key.strip()] = None
    return mapping, index


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _read_secrets(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    values = {}
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, separator, value = stripped.partition("=")
        if separator:
            values[key.strip()] = value
    return values


def run_configuration_check(recipe_path: Path, secrets_path: Path) -> tuple[bool, str]:
    if not recipe_path.is_file():
        return False, "Configuration check failed"
    recipe = load_simple_yaml(recipe_path.read_text())
    proxy = recipe.get("proxy") or {}
    servers = recipe.get("servers") or {}
    registry = recipe.get("registry") or {}
    builder = recipe.get("builder") or {}
    web_hosts = _as_list(servers.get("web") if isinstance(servers, dict) else None)
    site_names = _as_list(proxy.get("hosts") or proxy.get("host"))
    secrets = _read_secrets(secrets_path)
    complete = (
        recipe.get("service") == SERVICE_NAME
        and recipe.get("image") == IMAGE_NAME
        and HOST_ADDRESS in web_hosts
        and all(name in site_names for name in PUBLIC_SITE_NAMES)
        and proxy.get("ssl") is True
        and proxy.get("app_port") == LISTENING_PORT
        and (proxy.get("healthcheck") or {}).get("path") == HEALTH_CHECK_PATH
        and registry.get("username") == REGISTRY_USERNAME
        and REGISTRY_PASSWORD_NAME in _as_list(registry.get("password"))
        and builder.get("arch") == IMAGE_ARCHITECTURE
        and bool(secrets.get(REGISTRY_PASSWORD_NAME))
    )
    if complete:
        return True, "Configuration check success"
    return False, "Configuration check failed"


def test_configuration_check_succeeds_offline():
    ok, message = run_configuration_check(RECIPE_PATH, SECRETS_FIXTURE)
    assert ok is True, message
    assert message == "Configuration check success"

    recipe = RECIPE_PATH.read_text()
    assert "138.201.118.229" in recipe
    assert "image.bondev.eu" in recipe
    assert "www.image.bondev.eu" in recipe
    assert "shved270189/image_compressor" in recipe
    assert "username: shved270189" in recipe
    assert "ssl: true" in recipe
    assert "service: image_compressor" in recipe
    assert "arch: amd64" in recipe
    assert "app_port: 8000" in recipe
    assert "path: /api/health" in recipe
    assert "KAMAL_REGISTRY_PASSWORD" in recipe
    assert "test-registry-password" not in recipe

    secrets = SECRETS_FIXTURE.read_text()
    assert "KAMAL_REGISTRY_PASSWORD=test-registry-password" in secrets
