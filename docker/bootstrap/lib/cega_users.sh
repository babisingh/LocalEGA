#!/usr/bin/env bash
set -e

echomsg "Generating fake Central EGA users"

[[ -x $(readlink ${OPENSSL}) ]] && echo "${OPENSSL} is not executable. Adjust the setting with --openssl" && exit 3

mkdir -p ${PRIVATE}/cega/users

EGA_USER_PASSWORD_JOHN=$(generate_password 16)
EGA_USER_PASSWORD_JANE=$(generate_password 16)
EGA_USER_PASSWORD_TAYLOR=$(generate_password 16)

EGA_USER_PUBKEY_JOHN=${PRIVATE}/cega/users/john.pub
EGA_USER_SECKEY_JOHN=${PRIVATE}/cega/users/john.sec

EGA_USER_PUBKEY_JANE=${PRIVATE}/cega/users/jane.pub
EGA_USER_SECKEY_JANE=${PRIVATE}/cega/users/jane.sec

${OPENSSL} genrsa -out ${EGA_USER_SECKEY_JOHN} -passout pass:${EGA_USER_PASSWORD_JOHN} 2048
${OPENSSL} rsa -in ${EGA_USER_SECKEY_JOHN} -passin pass:${EGA_USER_PASSWORD_JOHN} -pubout -out ${EGA_USER_PUBKEY_JOHN}
chmod 400 ${EGA_USER_SECKEY_JOHN}

${OPENSSL} genrsa -out ${EGA_USER_SECKEY_JANE} -passout pass:${EGA_USER_PASSWORD_JANE} 2048
${OPENSSL} rsa -in ${EGA_USER_SECKEY_JANE} -passin pass:${EGA_USER_PASSWORD_JANE} -pubout -out ${EGA_USER_PUBKEY_JANE}
chmod 400 ${EGA_USER_SECKEY_JANE}

cat > ${PRIVATE}/cega/users/john.yml <<EOF
---
password_hash: $(${OPENSSL} passwd -1 ${EGA_USER_PASSWORD_JOHN})
pubkey: $(ssh-keygen -i -mPKCS8 -f ${EGA_USER_PUBKEY_JOHN})
EOF

cat > ${PRIVATE}/cega/users/jane.yml <<EOF
---
pubkey: $(ssh-keygen -i -mPKCS8 -f ${EGA_USER_PUBKEY_JANE})
EOF

cat > ${PRIVATE}/cega/users/taylor.yml <<EOF
---
password_hash: $(${OPENSSL} passwd -1 ${EGA_USER_PASSWORD_TAYLOR})
EOF

mkdir -p ${PRIVATE}/cega/users/{swe1,fin1}
# They all have access to SWE1
( # In a subshell
    cd ${PRIVATE}/cega/users/swe1
    ln -s ../john.yml .
    ln -s ../jane.yml .
    ln -s ../taylor.yml .
)
# John has also access to FIN1
(
    cd ${PRIVATE}/cega/users/fin1
    ln -s ../john.yml .
)

cat >> ${PRIVATE}/cega/.trace <<EOF
#####################################################################
#
# Generated by bootstrap/lib/cega_users.sh
#
#####################################################################
#
EGA_USER_PASSWORD_JOHN    = ${EGA_USER_PASSWORD_JOHN}
EGA_USER_PUBKEY_JOHN      = ./private/cega/users/john.pub
EGA_USER_PUBKEY_JANE      = ./private/cega/users/jane.pub
EGA_USER_PASSWORD_TAYLOR  = ${EGA_USER_PASSWORD_TAYLOR}
# =============================
EOF
