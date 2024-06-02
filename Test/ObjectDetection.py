from ikomia.dataprocess.workflow import Workflow
from ikomia.utils.displayIO import display

# Init your workflow
wf = Workflow()    

# Add the Grounding DINO Object Detector
dino = wf.add_task(name="infer_grounding_dino", auto_connect=True)

dino.set_parameters({
    "model_name": "Swin-B",
    "prompt": "wad",
    "conf_thres": "0.35",
    "conf_thres_text": "0.25"
})

# Run on your image  
wf.run_on(path="wads.jpg")
wf.run_on(path="wads.jpg")
#wf.run_on(url="https://raw.githubusercontent.com/Ikomia-dev/notebooks/main/examples/img/img_work.jpg")

# Inspect your results
display(dino.get_image_with_graphics())
