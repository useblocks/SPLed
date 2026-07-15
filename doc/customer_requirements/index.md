# Customer Requirements

## Customer A - Disco Light

Customer A requests a Disco Light that shall offer an ambient lighting experience that resonates with the rhythm of the surroundings.

```{if} var.features.CUSTOMER == "A"
This documentation is being built for **Customer A**, the exclusive commissioner of the Disco Light variant.
```

```{req} Sync light to ambient music
:id: REQ_DISCO_001
:status: open
:tags: customer-a, disco
:covered_by:

The lighting shall automatically sync with any ambient music, adjusting its blink rate to match the beats or rhythm.
```

```{req} Support chosen or randomized color
:id: REQ_DISCO_002
:status: open
:tags: customer-a, disco
:covered_by:

Users shall have the freedom to choose a specific color for the light. However, in the absence of a user-defined color, the software shall delight the user with randomized colors, ensuring an authentic disco experience.
```

```{req} Provide instantaneous light transitions
:id: REQ_DISCO_003
:status: open
:tags: customer-a, disco
:covered_by:

As the essence of a disco environment is dynamic and lively, light transitions shall happen instantaneously without any lag.
```

```{req} Ensure vibrant illumination
:id: REQ_DISCO_004
:status: open
:tags: customer-a, disco
:covered_by: SWDD_BC-100, SWDD_BC-202

The illumination provided shall be vibrant and noticeable, ranging from medium to high levels to keep up with the lively ambiance of disco settings.
```

## Customer B - Sleep Light

Customer B requests a sleep light offering an ambient lighting experience that facilitate a calm and restful environment.

```{if} var.features.CUSTOMER == "B"
This documentation is being built for **Customer B**, the exclusive commissioner of the Sleep Light variant.
```

```{req} Keep light constant without blink
:id: REQ_SLEEP_001
:status: open
:tags: customer-b, sleep
:covered_by: SWDD_LC-100

The light emitted shall be constant without any blink, ensuring a non-disruptive environment for rest.
```

```{req} Use warm white fixed color
:id: REQ_SLEEP_002
:status: open
:tags: customer-b, sleep
:covered_by: SWDD_LC-102, SWDD_LC-103

Color of the light shall be fixed to a warm white, known for its soothing and calming properties.
```

```{req} Support adjustable brightness
:id: REQ_SLEEP_003
:status: open
:tags: customer-b, sleep
:covered_by: SWDD_BC-100, SWDD_BC-101, SWDD_BC-102

The brightness of the light shall be adjustable.
```

```{req} Use blue light color
:id: REQ_SLEEP_004
:status: open
:tags: customer-b, sleep
:covered_by: SWDD_LC-102, SWDD_LC-103

The light color shall be blue.
```

## Customer C - Spa Light

Customer C requests a spa light encapsulating a tranquil and rejuvenating experience, reminiscent of real-world spa environments.

```{if} var.features.CUSTOMER == "C"
This documentation is being built for **Customer C**, the exclusive commissioner of the Spa Light variant.
```

```{req} Use slow rhythmic blink
:id: REQ_SPA_001
:status: open
:tags: customer-c, spa
:covered_by: SWDD_LC-101, SWDD_LC-203

The light shall have a slow, rhythmic blink that gives a sensation of calm and peace.
```

```{req} Cycle through predefined relaxing colors
:id: REQ_SPA_002
:status: open
:tags: customer-c, spa
:covered_by: SWDD_LC-102, SWDD_LC-202

Instead of a single color, the lighting shall cycle through multiple predefined colors that are commonly associated with relaxation and tranquility.
```

```{req} Ensure smooth color transitions
:id: REQ_SPA_003
:status: open
:tags: customer-c, spa
:covered_by: SWDD_LC-200, SWDD_LC-300

Transitions between colors shall be smooth and seamless, ensuring a continuous flow of relaxation.
```

```{req} Support adjustable brightness for spa mode
:id: REQ_SPA_004
:status: open
:tags: customer-c, spa
:covered_by: SWDD_BC-100, SWDD_BC-101, SWDD_BC-102

The brightness of the light shall be adjustable.
```
