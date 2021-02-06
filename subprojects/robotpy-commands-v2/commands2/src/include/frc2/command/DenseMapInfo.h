
#pragma once

#include <memory>
#include <wpi/DenseMapInfo.h>

#include <frc2/command/InstantCommand.h>
#include <frc2/command/Subsystem.h>

#include <stdio.h>

namespace wpi {

// Provide DenseMapInfo for command and subsystem
template<>
struct DenseMapInfo<std::shared_ptr<frc2::Command>> {

  using T = frc2::Command;

  static inline std::shared_ptr<T> getEmptyKey() {
    static auto empty = std::make_shared<frc2::InstantCommand>();
    return empty;
  }

  static inline std::shared_ptr<T> getTombstoneKey() {
    static auto tombstone = std::make_shared<frc2::InstantCommand>();
    return tombstone;
  }

  static unsigned getHashValue(const std::shared_ptr<T> PtrVal) {
    return (unsigned((uintptr_t)PtrVal.get()) >> 4) ^
           (unsigned((uintptr_t)PtrVal.get()) >> 9);
  }

  static bool isEqual(const std::shared_ptr<T> LHS, const std::shared_ptr<T> RHS) { return LHS == RHS; }

  // support find_as

  static unsigned getHashValue(const T* PtrVal) {
    return (unsigned((uintptr_t)PtrVal) >> 4) ^
           (unsigned((uintptr_t)PtrVal) >> 9);
  }

  static bool isEqual(const T* LHS, const std::shared_ptr<T> RHS) { return LHS == RHS.get(); }
  
};

template<>
struct DenseMapInfo<std::shared_ptr<frc2::Subsystem>> {

  using T = frc2::Subsystem;

  static inline std::shared_ptr<T> getEmptyKey() {
    static auto empty = std::make_shared<T>();
    return empty;
  }

  static inline std::shared_ptr<T> getTombstoneKey() {
    static auto tombstone = std::make_shared<T>();
    return tombstone;
  }

  static unsigned getHashValue(const std::shared_ptr<T> PtrVal) {
    return (unsigned((uintptr_t)PtrVal.get()) >> 4) ^
           (unsigned((uintptr_t)PtrVal.get()) >> 9);
  }

  static bool isEqual(const std::shared_ptr<T> LHS, const std::shared_ptr<T> RHS) { return LHS == RHS; }

  // support find_as

  static unsigned getHashValue(const T* PtrVal) {
    return (unsigned((uintptr_t)PtrVal) >> 4) ^
           (unsigned((uintptr_t)PtrVal) >> 9);
  }

  static bool isEqual(const T* LHS, const std::shared_ptr<T> RHS) { return LHS == RHS.get(); }
};


}; // namespace wpi