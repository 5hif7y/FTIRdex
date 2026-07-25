/* =========================================================================
    FTIRdex - Native C Unit Tests (Unity Framework)
========================================================================= */

#include "unity.h"
#include <string.h>
#include <stdlib.h>

// Struct simulation for functional groups
typedef struct {
    char name[64];
    int min_val;
    int max_val;
    int enabled;
} FuncGroup;

void setUp(void)
{
    // Setup resources before each test
}

void tearDown(void)
{
    // Clean resources after each test
}

// Test 1: Verify ftirzip extension checking logic
void test_ftirzip_extension_validation(void)
{
    const char* filename1 = "proyecto1.ftirzip";
    const char* filename2 = "proyecto2.txt";
    
    int len1 = (int)strlen(filename1);
    int is_zip1 = (len1 >= 8 && _stricmp(filename1 + len1 - 8, ".ftirzip") == 0);
    
    int len2 = (int)strlen(filename2);
    int is_zip2 = (len2 >= 8 && _stricmp(filename2 + len2 - 8, ".ftirzip") == 0);
    
    TEST_ASSERT_TRUE(is_zip1);
    TEST_ASSERT_FALSE(is_zip2);
}

// Test 2: Verify Functional Group Range Validation
void test_functional_group_range_matching(void)
{
    FuncGroup oh_group;
    strncpy(oh_group.name, "O-H (alcoholes)", sizeof(oh_group.name) - 1);
    oh_group.min_val = 3200;
    oh_group.max_val = 3600;
    oh_group.enabled = 1;
    
    int peak_wavenumber = 3400;
    int in_range = (peak_wavenumber >= oh_group.min_val && peak_wavenumber <= oh_group.max_val);
    
    TEST_ASSERT_EQUAL_STRING("O-H (alcoholes)", oh_group.name);
    TEST_ASSERT_TRUE(in_range);
}

// Test 3: Verify Sample filename extraction
void test_sample_filename_extraction(void)
{
    const char* full_path = "C:\\Datos\\FTIR\\Muestra_GO_lav.txt";
    const char* fname = strrchr(full_path, '\\');
    if (!fname) fname = strrchr(full_path, '/');
    if (fname) fname++; else fname = full_path;
    
    TEST_ASSERT_EQUAL_STRING("Muestra_GO_lav.txt", fname);
}

int main(void)
{
    UNITY_BEGIN();
    RUN_TEST(test_ftirzip_extension_validation);
    RUN_TEST(test_functional_group_range_matching);
    RUN_TEST(test_sample_filename_extraction);
    return UNITY_END();
}
