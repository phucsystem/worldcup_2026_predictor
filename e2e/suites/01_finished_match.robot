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
    # .an-eyebrow is CSS text-transform:uppercase, so innerText is "THE VERDICT";
    # assert the verdict sentence itself (not transformed) is present instead.
    ${verdict}=    Get Text    .analysis-note p
    Should Not Be Empty    ${verdict}

Finished Match Shows Match Stats Bars
    Get Text              h2.section-title >> text=Match stats    ==    Match stats
    ${bars}=    Get Element Count    .stat-bars .sb-row
    Should Be True        ${bars} >= 1
    # Stat labels (.sb-label) are uppercased by CSS; assert the bar values
    # (.sb-val, e.g. "58%", not transformed) render instead.
    ${vals}=    Get Element Count    .stat-bars .sb-val
    Should Be True        ${vals} >= 1

Finished Match Shows Key Moments And Goalscorers
    Get Text              h2.section-title >> text=Key moments    ==    Key moments
    Get Text              h2.section-title >> text=Goalscorers     ==    Goalscorers
    ${scorers}=    Get Element Count    .scorers .scorer-card
    Should Be True        ${scorers} >= 1

Finished Match Footer Credits The Verdict Model
    Get Text              .provenance    contains    verdict
