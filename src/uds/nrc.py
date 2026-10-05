"""VULCAN - UDS service names and Negative Response Codes (ISO 14229).

Two lookup tables used across the UDS tooling:
  SERVICES : request SID -> human name (positive response = SID + 0x40).
  NRC      : negative-response code -> human name.

The NRC is the fuzzer's key feedback signal (Phase 3): the way an ECU *refuses*
a request often leaks as much as an accepted one.
"""
from __future__ import annotations

# --- UDS service identifiers (SID). Positive response SID = request SID + 0x40. ---
SERVICES: dict[int, str] = {
    0x10: "DiagnosticSessionControl",
    0x11: "ECUReset",
    0x14: "ClearDiagnosticInformation",
    0x19: "ReadDTCInformation",
    0x22: "ReadDataByIdentifier",
    0x23: "ReadMemoryByAddress",
    0x24: "ReadScalingDataByIdentifier",
    0x27: "SecurityAccess",
    0x28: "CommunicationControl",
    0x2A: "ReadDataByPeriodicIdentifier",
    0x2C: "DynamicallyDefineDataIdentifier",
    0x2E: "WriteDataByIdentifier",
    0x2F: "InputOutputControlByIdentifier",
    0x31: "RoutineControl",
    0x34: "RequestDownload",
    0x35: "RequestUpload",
    0x36: "TransferData",
    0x37: "RequestTransferExit",
    0x3D: "WriteMemoryByAddress",
    0x3E: "TesterPresent",
    0x83: "AccessTimingParameter",
    0x84: "SecuredDataTransmission",
    0x85: "ControlDTCSetting",
    0x86: "ResponseOnEvent",
    0x87: "LinkControl",
}

# --- Negative Response Codes (NRC), returned as: 0x7F <SID> <NRC> ---
NRC: dict[int, str] = {
    0x10: "generalReject",
    0x11: "serviceNotSupported",
    0x12: "subFunctionNotSupported",
    0x13: "incorrectMessageLengthOrInvalidFormat",
    0x14: "responseTooLong",
    0x21: "busyRepeatRequest",
    0x22: "conditionsNotCorrect",
    0x24: "requestSequenceError",
    0x25: "noResponseFromSubnetComponent",
    0x26: "failurePreventsExecutionOfRequestedAction",
    0x31: "requestOutOfRange",
    0x33: "securityAccessDenied",
    0x34: "authenticationRequired",
    0x35: "invalidKey",
    0x36: "exceedNumberOfAttempts",
    0x37: "requiredTimeDelayNotExpired",
    0x70: "uploadDownloadNotAccepted",
    0x71: "transferDataSuspended",
    0x72: "generalProgrammingFailure",
    0x73: "wrongBlockSequenceCounter",
    0x78: "requestCorrectlyReceived-ResponsePending",
    0x7E: "subFunctionNotSupportedInActiveSession",
    0x7F: "serviceNotSupportedInActiveSession",
    0x81: "rpmTooHigh",
    0x83: "engineIsRunning",
    0x85: "voltageTooHigh",
    0x86: "voltageTooLow",
}

# Diagnostic session types (0x10 sub-function).
SESSIONS: dict[int, str] = {
    0x01: "default",
    0x02: "programming",
    0x03: "extendedDiagnostic",
    0x04: "safetySystem",
}


def service_name(sid: int) -> str:
    return SERVICES.get(sid, f"unknown(0x{sid:02X})")


def nrc_name(code: int) -> str:
    return NRC.get(code, f"unknown(0x{code:02X})")
