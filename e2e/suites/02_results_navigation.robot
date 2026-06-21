*** Settings ***
Documentation     Regression fix: a "Latest Results" row navigates to the match
...               page (/match/{id}), not the daily brief (/brief/{date}).
Resource          ../resources/common.resource
Suite Setup       Open WC26 Site
Suite Teardown    Close Browser

*** Test Cases ***
Latest Results Row Opens The Match Page
    Go To                   ${BASE_URL}/
    Wait For Elements State    .results-widget .match-row    visible    timeout=15s
    Click                   .results-widget .match-row >> nth=0
    Wait For Load State     networkidle    timeout=15s
    ${url}=    Get Url
    Should Contain          ${url}    /match/
    Should Not Contain      ${url}    /brief/

Opened Match Page Renders A Final-Score Hero
    Go To                   ${BASE_URL}/
    Wait For Elements State    .results-widget .match-row    visible    timeout=15s
    Click                   .results-widget .match-row >> nth=0
    Wait For Load State     networkidle    timeout=15s
    Get Element States      .next-match.is-final    then    bool(value & visible)
