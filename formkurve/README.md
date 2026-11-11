# Formkurve – Übungsvideos (Valentina, KI-generiert)

16 Übungen als nahtlose Endlosschleifen, ohne Ton und ohne Text.

- Format: 720×1248 (Hochformat, ca. 9:16), 24 fps, 3–10 s
- Dateien pro Übung: `<id>.mp4` (H.264, für alle Geräte), `<id>.webm` (VP9, kleiner), `<id>.jpg` (Vorschaubild)
- `manifest.json` enthält für jede Übung: deutscher und englischer Name, Muskeln, drei Technik-Hinweise, Kamerawinkel, Dauer

## Einbau (Web / React / PWA)

```html
<video autoplay muted loop playsinline preload="metadata" poster="goblet_squat.jpg">
  <source src="goblet_squat.webm" type="video/webm">
  <source src="goblet_squat.mp4" type="video/mp4">
</video>
```

`muted` und `playsinline` sind nötig, sonst spielt iOS das Video nicht automatisch ab.

```js
const { exercises } = await fetch('/videos/manifest.json').then(r => r.json());
const ex = exercises.find(e => e.id === 'romanian_deadlift');
// ex.de, ex.cues, ex.video_mp4, ex.poster ...
```

## Hinweis

Die Videos sind KI-generiert (Kennzeichnung `ai_generated: true` im Manifest).
In der App am besten kurz als «KI-Demo» kennzeichnen.
