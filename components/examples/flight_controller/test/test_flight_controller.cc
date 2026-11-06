/**
 * @file test_flight_controller.cc
 * @brief Unit and integration tests for flight_controller component, including direct testing of CheckAbort.
 */

#include <gtest/gtest.h>
#include <gmock/gmock.h>
using namespace testing;

extern "C"
{
#include "flight_controller.h"
#include "rte.h"

    bool_t CheckAbort(bool_t abort_commanded, bool_t valid_abort_command, bool_t off_course);
}

#include "mockup_components_examples_flight_controller.h"

struct CheckAbortParams
{
    bool_t abort_commanded;
    bool_t valid_abort_command;
    bool_t off_course;
    bool_t expected_result;
    const char *description;
};

inline std::ostream &operator<<(std::ostream &os, const CheckAbortParams &param)
{
    os << param.description;
    return os;
}

class CheckAbortTest : public TestWithParam<CheckAbortParams>
{
};

INSTANTIATE_TEST_SUITE_P(
    CheckAbortParamTests,
    CheckAbortTest,
    Values(
        CheckAbortParams{false, false, true, true, "Off course triggers abort"},
        CheckAbortParams{true, true, false, true, "Abort commanded and valid"},
        CheckAbortParams{true, false, false, false, "Abort commanded but not valid"},
        CheckAbortParams{false, false, false, false, "No abort and not off course"}));

// @need CheckAbortParamTests/CheckAbortTest.ReturnsExpectedResult/*, TS_FC-100, test, [SWDD_FC-100, SWDD_FC-101, SWDD_FC-102], CheckAbortParamTests/CheckAbortTest.ReturnsExpectedResult/Off course triggers abort\, CheckAbortParamTests/CheckAbortTest.ReturnsExpectedResult/Abort commanded and valid\, CheckAbortParamTests/CheckAbortTest.ReturnsExpectedResult/Abort commanded but not valid\, CheckAbortParamTests/CheckAbortTest.ReturnsExpectedResult/No abort and not off course
TEST_P(CheckAbortTest, ReturnsExpectedResult)
{
    // Arrange
    const auto &param = GetParam();

    // Act & Assert
    EXPECT_EQ(CheckAbort(param.abort_commanded, param.valid_abort_command, param.off_course), param.expected_result);
}

class FlightControllerTest : public TestWithParam<CheckAbortParams>
{
};

INSTANTIATE_TEST_SUITE_P(
    FlightControllerParamTests,
    FlightControllerTest,
    Values(
        CheckAbortParams{false, false, true, true, "Off course triggers abort"},
        CheckAbortParams{true, true, false, true, "Abort commanded and valid"},
        CheckAbortParams{true, false, false, false, "Abort commanded but not valid"},
        CheckAbortParams{false, false, false, false, "No abort and not off course"}));

// @need FlightControllerParamTests/FlightControllerTest.SetsExpectedSelfDestructState/*, TS_FC-001, test, [SWDD_FC-100, SWDD_FC-101, SWDD_FC-102, SWDD_FC-103, SWDD_FC-200, SWDD_FC-201, SWDD_FC-202, SWDD_FC-203, SWDD_FC-204], FlightControllerParamTests/FlightControllerTest.SetsExpectedSelfDestructState/Off course triggers abort\, FlightControllerParamTests/FlightControllerTest.SetsExpectedSelfDestructState/Abort commanded and valid\, FlightControllerParamTests/FlightControllerTest.SetsExpectedSelfDestructState/Abort commanded but not valid\, FlightControllerParamTests/FlightControllerTest.SetsExpectedSelfDestructState/No abort and not off course
TEST_P(FlightControllerTest, SetsExpectedSelfDestructState)
{
    // Arrange
    const auto &param = GetParam();

    CREATE_MOCK(mymock);
    // Set expectations for the mock RTE functions
    EXPECT_CALL(mymock, RteGetOffCourse(_))
        .WillOnce(SetArgPointee<0>(param.off_course));
    EXPECT_CALL(mymock, RteGetAbortCommanded())
        .WillOnce(Return(param.abort_commanded));
    EXPECT_CALL(mymock, RteGetValidAbortCommand())
        .WillOnce(Return(param.valid_abort_command));
    EXPECT_CALL(mymock, RteSetSelfDestructState(param.expected_result)).Times(1);

    // Act
    flightController();
}
