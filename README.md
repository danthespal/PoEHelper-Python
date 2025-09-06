# PoEHelper Auto-Flask

**PoEHelper** is an automation helper for **Path of Exile 2** that manages HP, MP, and ES flasks (or skills) based on configured thresholds and cooldowns. This documentation explains how to configure your `config.json`

---

## `config.json` Structure

`config.json` contains sections for HP, MP, and ES with the following fields:

```json
{
    "HP": {
        "enabled": true,
        "key": "1",
        "threshold": 90,
        "cooldown": 2.8,
        "post_use_delay": 0.5,
        "ignore_es": true,
        "note": "HP Flask triggers whenever life is below threshold regardless of ES. Set false for Lich/Eternal Life."
    },
    "MP": {
        "enabled": true,
        "key": "2",
        "threshold": 25,
        "cooldown": 3.5,
        "post_use_delay": 0.3,
        "note": "Mana Flask triggers when mana is at or below 25%."
    },
    "ES": {
        "enabled": true,
        "key": "E",
        "threshold": 40,
        "cooldown": 23,
        "post_use_delay": 0.0,
        "note": "ES Recovery Skill triggers when ES is at or below 40%."
    }
}
```

## Field Descriptions
| Field | Type |Description |
|:-----|:----:|:----------|
|`enabled`|boolean|Enable or disable this flask/skill.|
|`key`|string|Keyboard key assigned to this flask/skill.|
|`threshold`|int|Percentage threshold to trigger the flask (0-100).|
|`cooldown`|float|Cooldown in seconds between uses.|
|`post_use_delay`|float|Optional delay after using the flask before checking again.|
|`ignore_es`|boolean|HP only: If true, HP flask triggers regardless of ES. If false, triggers only when ES = 0 (for Lich/Eternal Life builds).|
|`note`|string|Optional explanation for reference.|

## Notes
```
ignore_es: true → HP flask triggers whenever life falls below the threshold.
ignore_es: false → HP flask triggers only when ES = 0, preventing misfires for builds where Life is frozen.
```