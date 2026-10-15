# Security

Please report security problems privately: GitHub's "Report a vulnerability" on this repository (Security tab), or
e-mail sandstonedevpsp@gmail.com. Do not open a public issue for them.

Relevant here: the setup script downloads PS2RC releases and verifies them against `skills/setup-ps2rc/ps2rc.lock.json`
(commit, content hash, SHA-256). A way to make it accept a tree or archive that does not match the lock, to write
outside the workspace, or to follow a link out of an archive is a security problem. Problems in the engine itself
belong to PS2RC's own security policy.

Never attach game files, disc images, generated code or builds to a report.
