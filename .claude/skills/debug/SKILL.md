---
name: debug
description: Structured diagnosis of a failure (an unexpected red test, a failing CI check, a runtime error). Use before changing code to fix it.
---

# Debug

When facing a failure, the most expensive mistake is to start changing things. Every blind change
adds a variable and makes the next diagnosis harder.

1. **Reproduce first.** A failure you cannot reproduce you cannot fix: you will only know it
   stopped showing up. The reproduction ends up as a test.
2. **Read the whole error**, including the full trace. The first line is usually the cause; the
   last one is only where it blew up.
3. **State one falsifiable hypothesis** and write it down: "I think X because Y".
4. **Make one change to test it.** If you change three things and it works, you do not know which
   one it was, and the other two stay in the code forever.
5. **If the hypothesis fails, discard it explicitly** and state another. Do not stack a new one on
   top.
6. **When it works, explain why.** A fix that works without knowing why is a latent failure.
7. **Leave the regression test** next to the fix, in the same `fix` commit, with the reason in the
   message body.

Warning sign: if you are several attempts in with the same fix slightly tweaked, the hypothesis is
wrong. Go back to step 2 and reread what the system is telling you.
