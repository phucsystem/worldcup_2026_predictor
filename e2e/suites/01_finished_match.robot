*** Settings ***
Documentation     New feature: the finished match page shows the verdict, match
...               statistics (incl. xG), key moments, and goalscorers.
Resource          ../resources/common.resource
Suite Setup       Open WC26 Site
Suite Teardown    Close Browser
Test Setup        Open Match Page

*** Test Cases ***
Finished Match Shows The Verdict
    Get Element States    .analysis-note            then    bool(value & visible)
    Get Text              .analysis-note .an-eyebrow    ==    The verdict
    ${verdict}=    Get Text    .analysis-note p
    Should Not Be Empty    ${verdict}

Finished Match Shows Match Stats Bars
    Get Text              h2.section-title >> text=Match stats    ==    Match stats
    ${bars}=    Get Element Count    .stat-bars .sb-row
    Should Be True        ${bars} >= 1
    Get Text              .stat-bars >> text=Possession    contains    Possession

Finished Match Shows Key Moments And Goalscorers
    Get Text              h2.section-title >> text=Key moments    ==    Key moments
    Get Text              h2.section-title >> text=Goalscorers     ==    Goalscorers
    ${scorers}=    Get Element Count    .scorers .scorer-card
    Should Be True        ${scorers} >= 1

Finished Match Footer Credits The Verdict Model
    Get Text              .provenance    contains    verdict
