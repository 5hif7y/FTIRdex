import os
import numpy as np
import pytest
from ftir_library import (
    load_data,
    plot_config,
    RAW,
    NONE,
    FTIR
)

# Test data files path
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "examples"))
JDX_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "muestras jdx"))

def test_load_data_formats():
    # Test loading FTIR text file
    ftir_file = os.path.join(DATA_DIR, "GO coque s lav ox.txt")
    if os.path.exists(ftir_file):
        x, y = load_data(ftir_file, FTIR)
        assert len(x) > 0
        assert len(y) == len(x)
        
    # Test auto-detection and loading JDX file
    jdx_file = os.path.join(JDX_DIR, "benzene-71-43-2-IR.jdx")
    if os.path.exists(jdx_file):
        x_jdx, y_jdx = load_data(jdx_file)
        assert len(x_jdx) > 0
        assert len(y_jdx) == len(x_jdx)

def test_plot_config_api():
    x = np.linspace(400, 4000, 500)
    y = np.sin(x/100) + np.random.normal(0, 0.05, len(x)) + 50.0 # simulates transmittance
    
    output_img = os.path.join(DATA_DIR, "images", "test_plot_config.png")
    os.makedirs(os.path.dirname(output_img), exist_ok=True)
    
    # Clean output image if it exists
    if os.path.exists(output_img):
        os.remove(output_img)
        
    # Test plot_config with actual algorithms
    plot_config(
        x, y, 
        smooth_algorithm="Savitzky_Golay(11, 2)", 
        baseline_algorithm="asls(lam=1e4)", 
        output_image=output_img,
        space="transmittance"
    )
    assert os.path.exists(output_img)
    os.remove(output_img)
    
    # Test plot_config with RAW/NONE constants
    plot_config(
        x, y,
        smooth_algorithm=RAW,
        baseline_algorithm=NONE,
        output_image=output_img,
        space="transmittance"
    )
    assert os.path.exists(output_img)
    os.remove(output_img)

    # Test plot_config with output_image passed as keyword argument at the end
    plot_config(
        x, y,
        RAW, NONE,
        space="transmittance",
        output_image=output_img
    )
    assert os.path.exists(output_img)
    os.remove(output_img)

    # Test plot_config with RAW/NONE and custom groups_db to check independent peak detection
    custom_db = {"Peak1": (1000, 2000)}
    plot_config(
        x, y,
        RAW, RAW,
        output_image=output_img,
        space="transmittance",
        groups_db=custom_db
    )
    assert os.path.exists(output_img)
    os.remove(output_img)

    # Test plot_config with output_image as the last positional argument
    plot_config(
        x, y,
        RAW, RAW,
        "transmittance",
        0.02,
        15,
        "lines",
        custom_db,
        None,
        True,
        output_img
    )
    assert os.path.exists(output_img)
    os.remove(output_img)

    # Test plot_config with custom groups_db but group_order=None, verifying it works
    plot_config(
        x, y,
        RAW, RAW,
        output_image=output_img,
        space="transmittance",
        groups_db=custom_db,
        group_order=None
    )
    assert os.path.exists(output_img)
    os.remove(output_img)

    # Test that missing output_image raises ValueError
    with pytest.raises(ValueError):
        plot_config(x, y, RAW, RAW)

def test_constants():
    assert RAW == "RAW"
    assert NONE == "NONE"
