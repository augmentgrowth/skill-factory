# Shared config graduation failure

Invoke graduate-skill Step 4 against a git-tracked skill with a committed root config.json and nested assets/config.json, an ignored personal config.json, and .env. Graduate to a fresh personal directory, then re-graduate after changing the shared config and ordinary files while the destination holds user-modified config.json and .env. Use paths containing spaces.

The previous Step 4 rsync excludes every config.json; fresh installation loses required shared configuration.
