# Hermes runbook: Hegel in Delhi

You operate this project for Welt. Claude writes the code and Hegel's material. You install it, run it, test it and report. Codex runs the Windows side on the PC (see `pc/CODEX.md`). Welt does what needs his hands or his login: GitHub settings, the BIOS, the router.

## Ground rules

- One task at a time, in order. Run its check, report, then wait for Welt's "go" before the next task.
- Report in Telegram: task name, ✅ or ❌, the key numbers. On failure, send the last 30 lines of output verbatim; don't paraphrase errors.
- Never commit secrets (keys, tokens, `~/.config/hegel/env`) or model files. Never force-push. Never rewrite history.
- Don't edit Hegel's material: `mind/soul.md`, `mind/owl.md`, `mind/situations.json`, `world/data/`, `docs/`. If something there looks wrong, report it instead. `docs/days/` is written by the world engine alone; never by hand.
- Configuration lives in `~/.config/hegel/env` on the Pi, never in the repo.
- If a step is ambiguous, ask Welt. Don't guess.

## Task 1: Repo and page

Welt sends you `hegel-in-delhi-repo.zip` on Telegram.

```bash
sudo apt-get update && sudo apt-get install -y git curl unzip wakeonlan python3
ssh-keygen -t ed25519 -N "" -C "hermes-pi hegel-in-delhi" -f ~/.ssh/hegel_deploy
cat >> ~/.ssh/config <<'EOF'
Host github-hegel
  HostName github.com
  User git
  IdentityFile ~/.ssh/hegel_deploy
  IdentitiesOnly yes
EOF
cat ~/.ssh/hegel_deploy.pub
```

Send Welt the public key line. He adds it at https://github.com/weltogeisto/hegel-in-delhi/settings/keys with "Allow write access" ticked. Wait for his "added".

```bash
ssh -T git@github-hegel    # prints "Hi weltogeisto/hegel-in-delhi! ..." and exits with 1; that is normal
git clone git@github-hegel:weltogeisto/hegel-in-delhi.git ~/hegel-in-delhi
cd ~/hegel-in-delhi
rm -rf /tmp/hegel-unzip && unzip -o <path-to>/hegel-in-delhi-repo.zip -d /tmp/hegel-unzip
cp -r /tmp/hegel-unzip/hegel-in-delhi/. .
git config user.name "Hermes for Welt"
git config user.email "weltogeisto@users.noreply.github.com"
git add -A
git commit -m "Day 1 prologue, mind bake-off, wake and sleep scripts"
git branch -M main
git push -u origin main
```

Then ask Welt to open https://github.com/weltogeisto/hegel-in-delhi/settings/pages and set: Source "Deploy from a branch", branch `main`, folder `/docs`, Save.

Check (allow up to ten minutes):

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://weltogeisto.github.io/hegel-in-delhi/
```

Done when it prints `200`. Report the URL.

## Task 2: The mind on the PC

Wake the PC the way you already do. Tell Welt that Codex should now work through `pc/CODEX.md`, steps 1–6. When Codex reports the MAC and IP (step 7), create the config:

```bash
mkdir -p ~/.config/hegel
cp ~/hegel-in-delhi/scripts/hegel.env.example ~/.config/hegel/env
nano ~/.config/hegel/env      # fill in PC_MAC, PC_HOST, PC_BCAST
source ~/.config/hegel/env
curl -s http://$PC_HOST:$MIND_PORT/health
```

Done when it prints `{"status":"ok"}`.

## Task 3: The bake-off

Bonsai must be running on the PC (port 8081).

```bash
cd ~/hegel-in-delhi && source ~/.config/hegel/env
python3 mind/bakeoff.py --url http://$PC_HOST:$MIND_PORT --label bonsai --only s01   # smoke test
python3 mind/bakeoff.py --url http://$PC_HOST:$MIND_PORT --label bonsai
```

Now ask Welt to have Codex stop Bonsai and start the Qwen server; the two don't fit in VRAM together. Then:

```bash
python3 mind/bakeoff.py --url http://$PC_HOST:$QWEN_PORT --label qwen
python3 mind/bakeoff.py --compare bonsai qwen
git add mind/results && git commit -m "Bake-off results" && git push
```

Send Welt the two summary lines and `mind/results/bakeoff.md` as a file. Ask Codex to restart Bonsai afterwards. Welt decides which model wins.

## Task 4: Wake and sleep

Prerequisites: Welt has enabled Wake on LAN in the BIOS and reserved the PC's IP in the router; Codex has finished `pc/CODEX.md` steps 7 and 8 with the 3-minute watchdog. Make sure `WATCHDOG_IDLE_MIN=3` in the env file.

```bash
cd ~/hegel-in-delhi
bash scripts/wake_cycle_test.sh 10
```

This takes about an hour. Send Welt the table. Done when all ten cycles show a wake time, an answer time and an "asleep after" time. Then ask Codex to re-register the watchdog with `-IdleMinutes 10`, and set `WATCHDOG_IDLE_MIN=10`.

## Task 5: The world engine

The engine is in the repo: `world/`, run as `python3 -m world`. Standard library only; nothing to install.

```bash
cd ~/hegel-in-delhi && git pull
python3 -m unittest discover -s tests          # prints OK
python3 -m world check                         # prints ok
python3 -m world simulate --date $(date -d tomorrow +%F)
```

The last command rehearses tomorrow offline with a stand-in mind and prints one summary line. Send it to Welt.

Now the dress rehearsal with the real mind. It runs a whole day through Bonsai, about 25 decisions, and takes 20 to 40 minutes of PC time. Nothing is pushed.

```bash
source ~/.config/hegel/env
python3 -m world simulate --date $(date -d tomorrow +%F) --mind http://$PC_HOST:$MIND_PORT --wake --feeds --out /tmp/hegel-dress
```

Send Welt the summary line and `/tmp/hegel-dress/days/<date>.json` as a file. The line counts steps, refusals (the world asked the mind to decide again) and quiet steps (no usable answer after three tries). Done when Welt has read the day and says go.

## Task 6: Shadow week

Hegel lives for a week on the `shadow` branch. The public page keeps replaying day 1; Welt watches the shadow at https://weltogeisto.github.io/hegel-in-delhi/?branch=shadow. The branch is public on GitHub but not on the page.

Add the engine's lines from `scripts/hegel.env.example` to `~/.config/hegel/env`, with `HEGEL_BRANCH=shadow` and `WATCHDOG_IDLE_MIN=10`. Then:

```bash
cd ~/hegel-in-delhi && git switch -c shadow && git push -u origin shadow
mkdir -p ~/.config/systemd/user
cp scripts/hegel-world.service scripts/hegel-world.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now hegel-world.timer
sudo loginctl enable-linger $USER              # keeps the timer running without a login
```

Then schedule the first shadow day. The world stays quiet until that midnight and begins cleanly:

```bash
python3 -m world start --date $(date -d tomorrow +%F)
python3 -m world status                        # "published to" shows that midnight
journalctl --user -u hegel-world -n 30
```

After the first midnight, "published to" stays ahead of now. Every morning, send Welt the `status` output. If "published to" is behind now, or "quiet steps" is above three, send the last 30 lines of `~/.local/state/hegel/world.log` verbatim.

To pause the world: `systemctl --user stop hegel-world.timer`. To resume: `start`. A pause longer than 45 minutes is picked up honestly: Hegel is at home when the world comes back, and nothing is invented for the gap.

## Task 7: The public switch

Welt decides when, and whether the shadow days become the archive.

```bash
systemctl --user stop hegel-world.timer
cd ~/hegel-in-delhi && git switch main && git pull
git merge shadow && git push                   # if Welt keeps the shadow days
python3 -m world start --date $(date -d tomorrow +%F)   # if Welt starts fresh instead
```

Set `HEGEL_BRANCH=main` in `~/.config/hegel/env`, then `systemctl --user start hegel-world.timer`. Check with `python3 -m world status`, and within fifteen minutes the public page shows "Live" under the map. Report the URL.
