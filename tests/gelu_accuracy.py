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


def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        library = Path(temp_dir) / "libgelu.so"

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

        errors = []

        print(f"{'Input':>10} {'Q8 Output':>12} "
              f"{'Float64':>12} {'Abs Error':>12}")

        for input_q8 in range(-1536, 1537):
            x = input_q8 / SCALE

            actual_q8 = gelu_q8(input_q8)
            actual = actual_q8 / SCALE

            expected = gelu_float64(x)
            error = abs(actual - expected)

            errors.append(error)

            if input_q8 % 128 == 0:
                print(f"{x:10.4f} {actual:12.6f} "
                      f"{expected:12.6f} {error:12.8f}")

        print("\nAccuracy Summary")
        print(f"Inputs tested: {len(errors)}")
        print(f"Maximum absolute error: {max(errors):.8f}")
        print(f"Mean absolute error: {sum(errors) / len(errors):.8f}")


if __name__ == "__main__":
    main()
