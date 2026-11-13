def build_condition_summary(prediction, features, crack, latest):
    status = prediction.get("status", "UNKNOWN")
    health = prediction.get("health", 0)
    crack_status = crack.get("status", "NO_IMAGE")
    temperature = latest.get("temperature", 0)

    if status == "SAFE":
        condition = "Bridge condition is stable under current monitoring data."
    elif status == "WARNING":
        condition = "Bridge requires attention. Early signs of abnormal vibration or visible damage may be present."
    elif status == "UNSAFE":
        condition = "Bridge condition is critical. Immediate engineering inspection is recommended."
    else:
        condition = "Bridge condition cannot be fully determined from the available data."

    recommendations = []
    if status == "UNSAFE":
        recommendations.extend(
            [
                "Restrict heavy vehicle movement until a structural engineer completes inspection.",
                "Perform detailed deck, girder, bearing, and expansion joint assessment.",
                "Repeat vibration testing with a calibrated sensor and compare against baseline frequency data.",
            ]
        )
    elif status == "WARNING":
        recommendations.extend(
            [
                "Schedule preventive maintenance inspection within the next maintenance window.",
                "Check bearings, joints, and support areas for looseness, corrosion, or settlement.",
                "Increase monitoring frequency and compare peak frequency changes over time.",
            ]
        )
    else:
        recommendations.extend(
            [
                "Continue routine monitoring and keep this reading as baseline history.",
                "Perform regular visual inspection after heavy rainfall, overload events, or seismic activity.",
            ]
        )

    if crack_status in {"HIGH", "MEDIUM"}:
        recommendations.append("Seal or repair detected cracks after measuring width, length, and depth on site.")
    elif crack_status == "LOW":
        recommendations.append("Mark the crack location and recheck during the next inspection cycle.")
    elif crack_status == "NO_IMAGE":
        recommendations.append("Upload a bridge surface image to include crack condition in the assessment.")

    if temperature and temperature > 45:
        recommendations.append("Review temperature effect on sensor readings and inspect expansion joints.")

    if features.get("peak_magnitude", 0) > 2.5 or features.get("std_dev", 0) > 0.08:
        recommendations.append("Investigate abnormal vibration amplitude and possible loose structural components.")

    return {
        "condition": condition,
        "priority": _priority(status, health, crack_status),
        "recommendations": recommendations,
    }


def _priority(status, health, crack_status):
    if status == "UNSAFE" or crack_status == "HIGH" or health < 45:
        return "Immediate"
    if status == "WARNING" or crack_status == "MEDIUM" or health < 75:
        return "Preventive"
    return "Routine"
