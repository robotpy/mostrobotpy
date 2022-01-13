
#pragma once

#include <units/time.h>
#include <units/length.h>

struct SomeClass {
    static constexpr auto s_constant = 2_s;
    static constexpr auto ms_constant1 = 20_ms;
    static constexpr units::second_t ms_constant2 = 50_ms;

    bool checkDefaultByName1(units::second_t period = ms_constant1);
    bool checkDefaultByName2(units::second_t period = ms_constant2);
    bool checkDefaultByNum(units::second_t period = 50_ms);

    units::second_t ms2s(units::millisecond_t ms);

    static constexpr units::foot_t five_ft = 5_ft;

    units::meter_t ft2m(units::foot_t f);
};