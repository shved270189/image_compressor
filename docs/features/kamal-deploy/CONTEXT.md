---
status: Living
updated_at: "2026-09-13"
---

# Domain Context — kamal-deploy

## Glossary

- Configuration check — A local command that proves Deploy configuration is readable and complete without contacting the production host or the container registry. NOT a live publish.
- Deploy configuration — The committed publish recipe the Project owner prepares so a later live command can run: host address, Public site names, image name, registry username, service name `image_compressor`, image architecture amd64, listening port, health-check path, and HTTPS. NOT the live running site and NOT secret values.
- Image owner — The person processing their selected image in the form. NOT Project owner (the person preparing Deploy configuration).
- Project owner — The person who prepares Deploy configuration, holds secrets locally, runs the Configuration check, and will run the live publish later. NOT Image owner.
- Public site name — A hostname the Project owner intends visitors to open after a later publish (`image.bondev.eu` and `www.image.bondev.eu`). NOT a local development URL.
- Secrets file — The Project owner's local gitignored file `.kamal/secrets` that holds secret values such as the registry password. NOT committed Deploy configuration (which may contain only environment-variable names) and NOT an SSH private key that may stay in the machine's default agent.
