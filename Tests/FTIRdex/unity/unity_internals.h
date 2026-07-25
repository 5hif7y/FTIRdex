/* =========================================================================
    Unity Project - A Test Framework for C
    Copyright (c) 2007-26 Mike Karlesky, Mark VanderVoord, Greg Williams
    [MIT License]
========================================================================= */

#ifndef UNITY_INTERNALS_H
#define UNITY_INTERNALS_H

#include <stdio.h>
#include <setjmp.h>
#include <math.h>
#include <stddef.h>
#include <string.h>
#include <limits.h>

/* Unity Details Set for 32/64 bit platforms */
typedef void (*UnityTestFunction)(void);

#define UNITY_DISPLAY_STYLE_INT           0
#define UNITY_DISPLAY_STYLE_UINT          1
#define UNITY_DISPLAY_STYLE_HEX8          2
#define UNITY_DISPLAY_STYLE_HEX16         3
#define UNITY_DISPLAY_STYLE_HEX32         4
#define UNITY_DISPLAY_STYLE_FLOAT         5

struct UNITY_STORAGE_T
{
    const char* TestFile;
    const char* CurrentTestName;
    unsigned int CurrentTestLineNumber;
    unsigned int NumberOfTests;
    unsigned int TestFailures;
    unsigned int TestIgnores;
    unsigned int CurrentTestFailed;
    unsigned int CurrentTestIgnored;
    jmp_buf AbortFrame;
};

extern struct UNITY_STORAGE_T Unity;

void UnityBegin(const char* filename);
int UnityEnd(void);
void UnityConcludeTest(void);
void UnityDefaultTestRun(UnityTestFunction Func, const char* FuncName, const int FuncLineNum);

void UnityAssertEqualNumber(const long expected,
                            const long actual,
                            const char* msg,
                            const unsigned int line,
                            const int style);

void UnityAssertEqualString(const char* expected,
                            const char* actual,
                            const char* msg,
                            const unsigned int line);

void UnityAssertEqualIntArray(const void* expected,
                              const void* actual,
                              const unsigned int num_elements,
                              const char* msg,
                              const unsigned int line,
                              const int style);

void UnityAssertBits(const long mask,
                     const long expected,
                     const long actual,
                     const char* msg,
                     const unsigned int line);

void UnityFail(const char* message, const unsigned int line);
void UnityIgnore(const char* message, const unsigned int line);

#endif /* UNITY_INTERNALS_H */
