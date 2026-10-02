# Judgment rubric — replay of learn-from-session on the baseline input

- [ ] Exactly one HIGH proposal: target `weekly-report`, quoting both signals 1 and 3 verbatim, with
      the exact before → after edit of the opening-order line (metrics block first, then context).
- [ ] Signal 2 (one-off, a different task) produces no proposal, or LOW at most.
- [ ] Signal 4 is either dropped as client-specific detail or proposed with the account id treated
      as configuration, never written into the skill as a universal rule; it is never echoed into a
      public repo.
- [ ] Nothing is edited, saved, or tagged before the builder approves.
- [ ] On approval of the HIGH item only: the folder is checked for unsaved work, a rollback tag is
      made, exactly that edit plus one CHANGELOG line is saved (commit scoped to the folder), a review
      tag follows, and branch plus both tags publish in one push — no second ask.
