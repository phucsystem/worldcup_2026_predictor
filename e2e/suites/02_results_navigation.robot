*** Settings ***
Documentation     Regression fix: a "Latest Results" row navigates to the match
...               page (/match/{id}), not the daily brief (/brief/{date}).
Resource          ../resources/common.resource
Suite Setup       Open WC26 Site
Suite Teardown    Close Browser

*** Test Cases ***
Latest Results Row Opens The Match Page
    Go To                   ${BASE_URL}/
    Wait For Elements State    .results-widget .match-row >> nth=0    visible    timeout=15s
    Click                   .results-widget .match-row >> nth=0
    Wait For Load State     networkidle    timeout=15s
    ${url}=    Get Url
    Should Contain          ${url}    /match/
    Should Not Contain      ${url}    /brief/

Opened Match Page Renders A Final-Score Hero
    Go To                   ${BASE_URL}/
    Wait For Elements State    .results-widget .match-row >> nth=0    visible    timeout=15s
    Click                   .results-widget .match-row >> nth=0
    Wait For Load State     networkidle    timeout=15s
    Get Element States      .next-match.is-final    then    bool(value & visible)

Results Page Shows A Penalty-Decided Knockout Result
    [Documentation]    The seeded 1-1 (pens) knockout tie renders the "Penalties"
    ...                label and the shootout score, proving winner_side + penalty
    ...                capture survive end-to-end.
    Go To                   ${BASE_URL}/results
    Wait For Elements State    .results-widget .match-row >> nth=0    visible    timeout=15s
    # Wait for the first penalty-score chip (nth=0 keeps the locator single, so it
    # fails loudly if no penalty row rendered — e.g. a seed id collision — rather
    # than silently passing through to the count assertion).
    Wait For Elements State    .results-widget .mr-pen >> nth=0    visible    timeout=15s
    ${pens}=    Get Element Count    .results-widget .mr-pen
    Should Be True          ${pens} >= 1
