/* =========================================================================
    Unity Project - A Test Framework for C
    Copyright (c) 2007-26 Mike Karlesky, Mark VanderVoord, Greg Williams
    [MIT License]
========================================================================= */

#include "unity.h"
#include <stdio.h>

struct UNITY_STORAGE_T Unity;

void UnityBegin(const char* filename)
{
    Unity.TestFile = filename;
    Unity.CurrentTestName = NULL;
    Unity.CurrentTestLineNumber = 0;
    Unity.NumberOfTests = 0;
    Unity.TestFailures = 0;
    Unity.TestIgnores = 0;
    Unity.CurrentTestFailed = 0;
    Unity.CurrentTestIgnored = 0;
    
    printf("=====================================================\n");
    printf("  Unity Test Suite: %s\n", filename);
    printf("=====================================================\n");
}

int UnityEnd(void)
{
    printf("-----------------------------------------------------\n");
    printf("%u Tests %u Failures %u Ignored\n", Unity.NumberOfTests, Unity.TestFailures, Unity.TestIgnores);
    if (Unity.TestFailures == 0)
    {
        printf("OK\n");
    }
    else
    {
        printf("FAIL\n");
    }
    printf("=====================================================\n");
    return (int)Unity.TestFailures;
}

void UnityConcludeTest(void)
{
    if (Unity.CurrentTestIgnored)
    {
        Unity.TestIgnores++;
    }
    else if (Unity.CurrentTestFailed)
    {
        Unity.TestFailures++;
    }
}

void UnityDefaultTestRun(UnityTestFunction Func, const char* FuncName, const int FuncLineNum)
{
    Unity.CurrentTestName = FuncName;
    Unity.CurrentTestLineNumber = (unsigned int)FuncLineNum;
    Unity.NumberOfTests++;
    Unity.CurrentTestFailed = 0;
    Unity.CurrentTestIgnored = 0;

    if (setjmp(Unity.AbortFrame) == 0)
    {
        setUp();
        Func();
    }
    tearDown();
    UnityConcludeTest();
}

void UnityAssertEqualNumber(const long expected, const long actual, const char* msg, const unsigned int line, const int style)
{
    if (expected != actual)
    {
        Unity.CurrentTestFailed = 1;
        printf("%s:%u:%s:FAIL: Expected %ld Was %ld", Unity.TestFile, line, Unity.CurrentTestName, expected, actual);
        if (msg) printf(" (%s)", msg);
        printf("\n");
        longjmp(Unity.AbortFrame, 1);
    }
    else
    {
        printf("%s:%u:%s:PASS\n", Unity.TestFile, line, Unity.CurrentTestName);
    }
}

void UnityAssertEqualString(const char* expected, const char* actual, const char* msg, const unsigned int line)
{
    if (expected == NULL && actual == NULL) return;
    if (expected == NULL || actual == NULL || strcmp(expected, actual) != 0)
    {
        Unity.CurrentTestFailed = 1;
        printf("%s:%u:%s:FAIL: Expected '%s' Was '%s'", Unity.TestFile, line, Unity.CurrentTestName, expected ? expected : "NULL", actual ? actual : "NULL");
        if (msg) printf(" (%s)", msg);
        printf("\n");
        longjmp(Unity.AbortFrame, 1);
    }
    else
    {
        printf("%s:%u:%s:PASS\n", Unity.TestFile, line, Unity.CurrentTestName);
    }
}

void UnityFail(const char* message, const unsigned int line)
{
    Unity.CurrentTestFailed = 1;
    printf("%s:%u:%s:FAIL: %s\n", Unity.TestFile, line, Unity.CurrentTestName, message ? message : "Assertion Failed");
    longjmp(Unity.AbortFrame, 1);
}

void UnityIgnore(const char* message, const unsigned int line)
{
    Unity.CurrentTestIgnored = 1;
    printf("%s:%u:%s:IGNORE: %s\n", Unity.TestFile, line, Unity.CurrentTestName, message ? message : "Test Ignored");
    longjmp(Unity.AbortFrame, 1);
}
