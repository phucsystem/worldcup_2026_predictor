*** Settings ***
Documentation     New feature: upcoming match pages show a "What fans are saying"
...               panel of auto-curated Reddit/Bluesky discussion, each item
...               linking back to its source. Backed by the seeded upcoming
...               fixture (app.data.seed_social_fixture, id 990002).
Resource          ../resources/common.resource
Suite Setup       Open WC26 Site
Suite Teardown    Close Browser
Test Setup        Open Match Page    ${SOCIAL_FIXTURE_ID}

*** Variables ***
${SOCIAL_FIXTURE_ID}    990002

*** Test Cases ***
Upcoming Match Shows The Fan Discussion Panel
    Get Element States    .social-highlights        then    bool(value & visible)
    ${items}=    Get Element Count    .social-highlights .sh-item
    Should Be True        ${items} >= 1

Highlights Link Back To Source Safely
    # Every source link opens in a new tab with rel="noopener nofollow".
    ${links}=    Get Element Count    .social-highlights a.sh-link
    Should Be True        ${links} >= 1
    ${rel}=    Get Attribute    .social-highlights a.sh-link >> nth=0    rel
    Should Contain        ${rel}    noopener
    Should Contain        ${rel}    nofollow
    ${href}=    Get Attribute    .social-highlights a.sh-link >> nth=0    href
    Should Match Regexp    ${href}    ^https?://

Finished Match Hides The Fan Discussion Panel
    # The panel is an upcoming-match feature; it must not appear on a finished match.
    Open Match Page    ${FIXTURE_ID}
    ${panels}=    Get Element Count    .social-highlights
    Should Be Equal As Integers    ${panels}    0
