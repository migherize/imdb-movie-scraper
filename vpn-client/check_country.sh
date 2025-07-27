#!/bin/bash

EXPECTED="United States"
IP=$(curl -s https://api.ipify.org)
COUNTRY=$(curl -s https://ipapi.co/$IP/country_name/)

if [[ "$COUNTRY" == "$EXPECTED" ]]; then
    echo "✅ Connected to $COUNTRY"
    exit 0
else
    echo "❌ Connected to wrong country: $COUNTRY"
    exit 1
fi
