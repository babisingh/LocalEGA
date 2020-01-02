prepare-users:
	@mkdir -p ../private/users
	@test -e ../private/users/serial || echo '15000' > ../private/users/serial

../private/users/%.sshkey: ../private/users/%.passphrase
	@echo "Creating $(@F)"
	@ssh-keygen -t ed25519 -f $@ -N "$(file < $<)" -C "$(@:../private/users/%.sshkey=%)@LocalEGA" &>/dev/null
	@chmod 400 $@
# Making the key readable, because when it's injected inside the container
# it retains the permissions. Therefore, originally 400, will make it unreadable to the lega user.

../private/users/%.json: ../private/users/%.sshkey
	@mkdir -p $(@D)
	@echo "Creating $(@F)"
	@python -m run.cega.user $(@:../private/users/%.json=%) $(file < ../private/users/serial) '$(@:.json=.passphrase)' < $(<:=.pub) > $@
	@$(file > ../private/users/serial,$(shell echo "$$(($(file < ../private/users/serial)+1))"))

../private/users/%.passphrase:
	@mkdir -p $(@D)
	@echo "Creating $(@F)"
	@python -m run.pwd_gen 8 > $@

clean-users:
	rm -rf ../private/users
