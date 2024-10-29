cat <<EOF > tinytuya.json
{
    "apiKey": "${SWITCH_API_KEY}",
    "apiSecret": "${SWITCH_API_SECRET}",
    "apiRegion": "us",
    "apiDeviceID": "${SWITCH_ID}"
}
EOF

poetry run python groundlight_light_alert/app.py