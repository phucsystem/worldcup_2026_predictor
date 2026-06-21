*** Settings ***
Documentation     Shared keywords + config for the WC26 Intelligence e2e suites.
Library           Browser

*** Variables ***
${BASE_URL}        http://localhost:3000
# The deterministic finished fixture inserted by app.data.seed_e2e_fixture.
${FIXTURE_ID}      990001
${HEADLESS}        ${True}

*** Keywords ***
Open WC26 Site
    New Browser    chromium    headless=${HEADLESS}
    New Context    viewport={'width': 1280, 'height': 900}
    New Page       ${BASE_URL}/

Open Match Page
    [Arguments]    ${fixture_id}=${FIXTURE_ID}
    Go To          ${BASE_URL}/match/${fixture_id}
    Wait For Load State    networkidle    timeout=15s
