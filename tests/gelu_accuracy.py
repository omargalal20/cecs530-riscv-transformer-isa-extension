import ctypes
import math
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GELU_DIR = ROOT / "kernels" / "gelu"

SCALE = 256


def gelu_float64(x):
    """Float64 GELU reference using the tanh approximation."""
    return 0.5 * x * (
        1.0 + math.tanh(
            0.7978845608 * (x + 0.044715 * x**3)
        )
    )


def compile_gelu():
    """Compile the fixed-point GELU implementation as a shared library."""
    temp_dir = tempfile.TemporaryDirectory()
    library = Path(temp_dir.name) / "libgelu.so"

    subprocess.run([
        "gcc", "-shared", "-fPIC", "-O2",
        "-DHOST_BUILD",
        "-I", str(GELU_DIR),
        str(GELU_DIR / "gelu.c"),
        "-o", str(library)
    ], check=True)

    lib = ctypes.CDLL(str(library))

    gelu_q8 = lib.gelu_baseline
    gelu_q8.argtypes = [ctypes.c_int32]
    gelu_q8.restype = ctypes.c_int32

    return gelu_q8, temp_dir


def print_header():
    print("=" * 72)
    print("             GELU FIXED-POINT ACCURACY TEST")
    print("=" * 72)
    print("Reference  : Float64 GELU (tanh approximation)")
    print("Test       : Q8 fixed-point vs. float64 reference")
    print("Input range: -6.0 to 6.0")
    print("Scale      : 256")
    print("-" * 72)
    print(f"{'Input':>12} {'Q8 Output':>14} "
          f"{'Float64 Ref':>14} {'Abs Error':>14}")
    print("-" * 72)


def print_summary(errors):
    print("-" * 72)
    print("ACCURACY SUMMARY")
    print("-" * 72)
    print(f"Total inputs tested       : {len(errors)}")
    print(f"Maximum absolute error    : {max(errors):.8f}")
    print(f"Mean absolute error       : {sum(errors) / len(errors):.8f}")
    print("=" * 72)


def main():
    gelu_q8, temp_dir = compile_gelu()

    try:
        print_header()
        errors = []

        for input_q8 in range(-1536, 1537):
            x = input_q8 / SCALE

            actual = gelu_q8(input_q8) / SCALE
            expected = gelu_float64(x)
            error = abs(actual - expected)

            errors.append(error)

            if input_q8 % 128 == 0:
                print(f"{x:12.4f} {actual:14.6f} "
                      f"{expected:14.6f} {error:14.8f}")

        print_summary(errors)

    finally:
        temp_dir.cleanup()


if __name__ == "__main__":
    main()
