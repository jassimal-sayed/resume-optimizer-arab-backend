PASSPHRASE='resume'; \     
printf '%s' "$PASSPHRASE" | gpg --batch --yes --pinentry-mode loopback --passphrase-fd 0 --symmetric --cipher-algo AES256 .env.prod
unset PASSPHRASE