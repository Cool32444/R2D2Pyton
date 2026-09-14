import Canvas
import HAC
import LifX

def get_canvas_data():
    return {
        f"The canvas data is, respond in CTE time: \n {Canvas.get_user_schedule_summary()}"
    }
def get_hac_data():
    return {
        f"""
        "The HAC data is: \n {HAC.get_hac_grades()}
        
        If asked for the grades, respond with the raw averages of each class.
        For AP and KAP classes, Majors are 70%, Minors are 20%, and Others are 10%.
        For ACA / Elective classes, Majors are 50%, Minors are 35%, and Others are 15%.
        """
    }
def control_lifx_lights(**kwargs):
    LifX.set_lifx_light_color(
        color=kwargs.get("color"),
        selector=kwargs.get("selector", "all"),
        brightness=kwargs.get("brightness"),
        power=kwargs.get("power"),
        duration=kwargs.get("duration", 1.0)
    )