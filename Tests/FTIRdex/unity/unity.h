/* =========================================================================
    Unity Project - A Test Framework for C
    Copyright (c) 2007-26 Mike Karlesky, Mark VanderVoord, Greg Williams
    [MIT License]
========================================================================= */

#ifndef UNITY_FRAMEWORK_H
#define UNITY_FRAMEWORK_H

#include "unity_internals.h"

#ifdef __cplusplus
extern "C"
{
#endif

void setUp(void);
void tearDown(void);

#define UNITY_BEGIN() UnityBegin(__FILE__)
#define UNITY_END()   UnityEnd()

#define RUN_TEST(func) UnityDefaultTestRun(func, #func, __LINE__)

#define TEST_FAIL_MESSAGE(message)           UnityFail((message), __LINE__)
#define TEST_IGNORE_MESSAGE(message)         UnityIgnore((message), __LINE__)

#define TEST_ASSERT_TRUE(condition)          if (!(condition)) UnityFail("Expected TRUE Was FALSE", __LINE__)
#define TEST_ASSERT_FALSE(condition)         if ((condition))  UnityFail("Expected FALSE Was TRUE", __LINE__)

#define TEST_ASSERT_EQUAL_INT(expected, actual)         UnityAssertEqualNumber((long)(expected), (long)(actual), NULL, __LINE__, UNITY_DISPLAY_STYLE_INT)
#define TEST_ASSERT_EQUAL_UINT(expected, actual)        UnityAssertEqualNumber((long)(expected), (long)(actual), NULL, __LINE__, UNITY_DISPLAY_STYLE_UINT)
#define TEST_ASSERT_EQUAL_STRING(expected, actual)      UnityAssertEqualString((const char*)(expected), (const char*)(actual), NULL, __LINE__)
#define TEST_ASSERT_EQUAL(expected, actual)             TEST_ASSERT_EQUAL_INT(expected, actual)

#define TEST_ASSERT(condition)                          TEST_ASSERT_TRUE(condition)

#ifdef __cplusplus
}
#endif

#endif /* UNITY_FRAMEWORK_H */
