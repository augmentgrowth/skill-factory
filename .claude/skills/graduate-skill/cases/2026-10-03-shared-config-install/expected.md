# Expected

Fresh install copies committed, non-ignored config.json at any depth. Ignored or untracked personal configuration and every .env stay behind. Reinstallation preserves all destination config.json and .env bytes, updates ordinary files, and removes stale ordinary files. Reject overlapping roots, symlinked roots/ancestors/tree entries, and special files before any destination mutation. No secret values appear in output.
