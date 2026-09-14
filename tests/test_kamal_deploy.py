import subprocess
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


def _missing_gaps(recipe_path: Path, secrets_path: Path) -> list[str]:
    if not recipe_path.is_file():
        return ["missing Deploy configuration"]
    recipe = load_simple_yaml(recipe_path.read_text())
    proxy = recipe.get("proxy") if isinstance(recipe.get("proxy"), dict) else {}
    servers = recipe.get("servers") if isinstance(recipe.get("servers"), dict) else {}
    registry = recipe.get("registry") if isinstance(recipe.get("registry"), dict) else {}
    builder = recipe.get("builder") if isinstance(recipe.get("builder"), dict) else {}
    healthcheck = proxy.get("healthcheck") if isinstance(proxy.get("healthcheck"), dict) else {}
    web_hosts = _as_list(servers.get("web"))
    site_names = _as_list(proxy.get("hosts") or proxy.get("host"))
    secrets = _read_secrets(secrets_path)
    gaps = []
    if recipe.get("service") != SERVICE_NAME:
        gaps.append("missing service name")
    if recipe.get("image") != IMAGE_NAME:
        gaps.append("missing image name")
    if HOST_ADDRESS not in web_hosts:
        gaps.append("missing host address")
    if any(name not in site_names for name in PUBLIC_SITE_NAMES):
        gaps.append("missing Public site name")
    if proxy.get("ssl") is not True:
        gaps.append("missing HTTPS")
    if proxy.get("app_port") is None:
        gaps.append("missing listening port")
    if healthcheck.get("path") is None:
        gaps.append("missing health-check path")
    if registry.get("username") != REGISTRY_USERNAME:
        gaps.append("missing registry username")
    if builder.get("arch") != IMAGE_ARCHITECTURE:
        gaps.append("missing image architecture")
    if not secrets.get(REGISTRY_PASSWORD_NAME):
        gaps.append("missing registry password from Secrets file")
    return gaps


def run_configuration_check(recipe_path: Path, secrets_path: Path) -> tuple[bool, str]:
    gaps = _missing_gaps(recipe_path, secrets_path)
    if gaps:
        return False, "Configuration check failed: " + ", ".join(gaps)
    recipe = load_simple_yaml(recipe_path.read_text())
    proxy = recipe.get("proxy") if isinstance(recipe.get("proxy"), dict) else {}
    registry = recipe.get("registry") if isinstance(recipe.get("registry"), dict) else {}
    healthcheck = proxy.get("healthcheck") if isinstance(proxy.get("healthcheck"), dict) else {}
    if REGISTRY_PASSWORD_NAME not in _as_list(registry.get("password")):
        return False, "Configuration check failed"
    violations = []
    if proxy.get("app_port") != LISTENING_PORT:
        violations.append("listening port does not match the application image")
    if healthcheck.get("path") != HEALTH_CHECK_PATH:
        violations.append("health-check path does not match the application image")
    if violations:
        return False, "Configuration check failed: " + ", ".join(violations)
    return True, "Configuration check success"


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


def test_configuration_check_names_missing_secrets(tmp_path):
    ok, message = run_configuration_check(RECIPE_PATH, tmp_path / "absent")
    assert ok is False
    assert "success" not in message.lower()
    assert "registry password" in message
    assert "Secrets file" in message


def test_configuration_check_names_missing_fields(tmp_path):
    recipe = tmp_path / "deploy.yml"
    recipe.write_text("builder:\n  arch: amd64\n")
    ok, message = run_configuration_check(recipe, SECRETS_FIXTURE)
    assert ok is False
    assert "success" not in message.lower()
    for term in (
        "host address",
        "Public site name",
        "image name",
        "registry username",
        "HTTPS",
        "service name",
        "listening port",
        "health-check path",
    ):
        assert term in message, term
    assert "SSH" not in message

    one_site = tmp_path / "one-site.yml"
    one_site.write_text(RECIPE_PATH.read_text().replace("    - www.image.bondev.eu\n", ""))
    ok, message = run_configuration_check(one_site, SECRETS_FIXTURE)
    assert ok is False
    assert "success" not in message.lower()
    assert "Public site name" in message


def test_secrets_file_is_gitignored():
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", ".kamal/secrets"],
        check=False,
    )
    assert ignored.returncode == 0


def test_committed_tree_has_no_secret_values():
    tracked = subprocess.check_output(["git", "ls-files"], text=True).splitlines()
    pem = "-----BEGIN " + "PRIVATE KEY-----"
    openssh = "-----BEGIN " + "OPENSSH PRIVATE KEY-----"
    rsa = "-----BEGIN " + "RSA PRIVATE KEY-----"
    for relative in tracked:
        text = Path(relative).read_text(errors="replace")
        assert pem not in text, relative
        assert openssh not in text, relative
        assert rsa not in text, relative
        if relative == "tests/fixtures/kamal/secrets":
            assert "KAMAL_REGISTRY_PASSWORD=test-registry-password" in text
            continue
        if relative.startswith("tests/"):
            continue
        assert "test-registry-password" not in text, relative


def test_recipe_port_and_path_match_application_image():
    recipe = load_simple_yaml(RECIPE_PATH.read_text())
    assert recipe["proxy"]["app_port"] == LISTENING_PORT
    assert recipe["proxy"]["healthcheck"]["path"] == HEALTH_CHECK_PATH
    assert recipe["registry"]["password"] == [REGISTRY_PASSWORD_NAME]


def test_mismatched_port_or_path_is_not_production_target(tmp_path):
    bad_port = tmp_path / "bad-port.yml"
    bad_port.write_text(RECIPE_PATH.read_text().replace("app_port: 8000", "app_port: 3000"))
    ok, message = run_configuration_check(bad_port, SECRETS_FIXTURE)
    assert ok is False
    assert "success" not in message.lower()
    assert "listening port" in message

    bad_path = tmp_path / "bad-path.yml"
    bad_path.write_text(RECIPE_PATH.read_text().replace("path: /api/health", "path: /"))
    ok, message = run_configuration_check(bad_path, SECRETS_FIXTURE)
    assert ok is False
    assert "success" not in message.lower()
    assert "health-check path" in message
