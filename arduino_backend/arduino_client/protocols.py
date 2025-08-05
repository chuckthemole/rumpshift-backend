import struct


def encode_message(command: str, payload: dict) -> bytes:
    # Simple example: 1-byte command + 2-byte integer payload
    cmd_code = {
        "start_pump": 0x01,
        "stop_pump":  0x02
    }.get(command, 0x00)

    # Just example payload, can be more complex
    duration = payload.get("duration", 0)
    return struct.pack("!BH", cmd_code, duration)
