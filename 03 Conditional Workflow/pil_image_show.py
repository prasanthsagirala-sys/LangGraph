from PIL import Image
import io

def imshow_raw(workflow):
    # Generate PNG bytes
    png_bytes = workflow.get_graph().draw_mermaid_png()   # <-- CALL the method ()

    # Load with Pillow
    img = Image.open(io.BytesIO(png_bytes))

    # Show the image
    img.show()