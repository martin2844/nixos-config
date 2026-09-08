# Retain the NixOS login environment when starting Zsh directly.
if [[ -z ${__ETC_PROFILE_DONE:-} ]]; then
  source /etc/profile
fi
