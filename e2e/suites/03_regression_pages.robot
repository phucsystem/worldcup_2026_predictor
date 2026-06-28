*** Settings ***
Documentation     Regression: the core pages still render after the changes.
Resource          ../resources/common.resource
Suite Setup       Open WC26 Site
Suite Teardown    Close Browser

*** Test Cases ***
Home Page Renders
    Go To       ${BASE_URL}/
    Wait For Load State    networkidle    timeout=15s
    Get Title   contains    WC26
    Get Text    .results-widget .rw-title    ==    Latest Results

Standings Page Renders
    Go To       ${BASE_URL}/standings
    Wait For Load State    networkidle    timeout=15s
    Get Title   contains    WC26
    Get Text    body    contains    Standings

Fixtures Page Renders
    Go To       ${BASE_URL}/fixtures
    Wait For Load State    networkidle    timeout=15s
    Get Title   contains    WC26

Knockout Page Renders
    Go To       ${BASE_URL}/knockout
    Wait For Load State    networkidle    timeout=15s
    Get Title   contains    WC26
    Get Text    body    contains    Knockout

Changelog Page Renders
    Go To       ${BASE_URL}/changelog
    Wait For Load State    networkidle    timeout=15s
    Get Text    body    contains    Changelog

Match Page Route Renders For The Seeded Fixture
    Open Match Page
    Get Element States    .next-match.is-final    then    bool(value & visible)
