# LimenOS — Scope of Use

LimenOS turns a Miyoo Flip into a portable security workstation. It is built
for **authorised** work:

- networks, devices and accounts **you own**
- engagements with **written** permission covering the specific targets
- CTFs, labs and teaching environments
- defensive work: auditing your own perimeter, verifying your own hardening

## Lines this project does not cross

- **No unattended attack modes.** Every action that touches something outside
  the device requires a human to press a button for *that* action. Nothing
  fires on a timer, a schedule or a trigger.
- **No jamming or denial of service.** No deauth floods dressed up as "stress
  testing", no RF jamming. That's spectrum interference, and it's illegal in
  every jurisdiction that matters.
- **No evasion tooling** whose only purpose is defeating detection.
- **Captures are evidence.** Treat the exFAT vault as containing other people's
  data. Scope it, retain it only as long as the engagement needs, destroy it
  afterwards.

## Things worth knowing before you carry it

- Monitor-mode capture is **passive** but is still interception in many
  jurisdictions. Passive is not automatically lawful.
- Injection, rogue APs and HID payloads are **active** and will be treated as
  intrusion attempts. Have your authorisation in writing, on you.
- Regulatory domain settings exist for a reason. Raising TX power or using
  channels outside your region's allocation is an offence independent of
  whatever you were testing.

If you are not sure a specific use is authorised, it isn't. Get it in writing.
