import marimo

__generated_with = "0.9.0"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    from core.io import load_from_upload, load_from_url
    from core.piv import PivConfig, PassConfig, run_pipeline
    return PassConfig, PivConfig, load_from_upload, load_from_url, mo, np, run_pipeline


@app.cell
def _(mo):
    mo.md("# PIV — tuning & batch (marimo boilerplate)")
    return


@app.cell
def _(mo):
    source_mode = mo.ui.radio(["Upload files", "URL (GCS/public)"], value="Upload files", label="Image source")
    uploader = mo.ui.file(filetypes=[".png", ".tif", ".tiff", ".jpg"], multiple=True, label="Frame pair(s)")
    url_a = mo.ui.text(label="Frame A URL", placeholder="https://storage.googleapis.com/bucket/frameA.tif")
    url_b = mo.ui.text(label="Frame B URL", placeholder="https://storage.googleapis.com/bucket/frameB.tif")
    setup_col = mo.vstack([mo.md("## 1 · Setup"), source_mode, uploader, url_a, url_b])
    return setup_col, source_mode, uploader, url_a, url_b


@app.cell
def _(load_from_upload, load_from_url, source_mode, uploader, url_a, url_b, mo):
    frame_a = frame_b = None
    load_error = None
    try:
        if source_mode.value == "Upload files" and uploader.value:
            imgs = load_from_upload(uploader.value)
            names = sorted(imgs)
            if len(names) >= 2:
                frame_a, frame_b = imgs[names[0]], imgs[names[1]]
        elif source_mode.value == "URL (GCS/public)" and url_a.value and url_b.value:
            frame_a = load_from_url(url_a.value)
            frame_b = load_from_url(url_b.value)
    except Exception as e:
        load_error = str(e)
    status = mo.md(
        "*load at least 2 frames above to begin*" if frame_a is None
        else f"loaded pair: {frame_a.shape} / {frame_b.shape}"
        if load_error is None else f"**error loading frames:** {load_error}"
    )
    return frame_a, frame_b, status


@app.cell
def _(status):
    status
    return


@app.cell
def _(mo):
    mode = mo.ui.radio(["Single-pass", "Multi-pass"], value="Single-pass", label="Mode")
    n_passes = mo.ui.number(2, 5, value=2, label="Number of passes", step=1)
    return mode, n_passes


@app.cell
def _(PassConfig, mode, n_passes, mo):
    n = 1 if mode.value == "Single-pass" else int(n_passes.value)
    pass_controls = []
    for i in range(n):
        default_win = max(16, 64 // (2 ** i))
        pass_controls.append({
            "window": mo.ui.slider(16, 128, value=default_win, step=16, label=f"Pass {i+1} · window size"),
            "overlap": mo.ui.slider(0, 96, value=default_win // 2, step=8, label=f"Pass {i+1} · overlap"),
            "search": mo.ui.slider(16, 192, value=default_win + 32, step=16, label=f"Pass {i+1} · search area"),
            "snr": mo.ui.slider(1.0, 3.0, value=1.3, step=0.1, label=f"Pass {i+1} · SNR threshold"),
            "interp": mo.ui.checkbox(True, label=f"Pass {i+1} · interpolate outliers"),
        })
    pass_cards = mo.accordion({
        f"Pass {i+1}": mo.vstack(list(c.values())) for i, c in enumerate(pass_controls)
    })
    tuning_col = mo.vstack([mo.md("## 2 · Tuning"), mode, n_passes if mode.value == "Multi-pass" else mo.md(""), pass_cards])
    return pass_cards, pass_controls, tuning_col


@app.cell
def _(PassConfig, PivConfig, pass_controls):
    piv_config = PivConfig(passes=[
        PassConfig(
            window_size=int(c["window"].value),
            overlap=int(c["overlap"].value),
            search_area=int(c["search"].value),
            snr_threshold=float(c["snr"].value),
            interpolate_outliers=bool(c["interp"].value),
        ) for c in pass_controls
    ])
    return (piv_config,)


@app.cell
def _(frame_a, frame_b, mo, piv_config, run_pipeline):
    preview = mo.md("*no result yet*")
    if frame_a is not None and frame_b is not None:
        try:
            results = run_pipeline(frame_a, frame_b, piv_config)
            last_cfg, u, v = results[-1]
            preview = mo.md(
                f"**Last pass result** — window {last_cfg.window_size}px, "
                f"field shape {u.shape}, mean |u|={abs(u).mean():.2f}px, mean |v|={abs(v).mean():.2f}px"
            )
        except Exception as e:
            preview = mo.md(f"**processing error:** {e}")
    return (preview,)


@app.cell
def _(mo, preview, tuning_col):
    mo.hstack([tuning_col, mo.vstack([mo.md("## 3 · Live preview"), preview])], widths=[1, 1])
    return


@app.cell
def _(mo):
    mo.md("## 4 · Batch")
    run_batch = mo.ui.run_button(label="Run batch with current settings")
    run_batch
    return (run_batch,)


@app.cell
def _(mo, run_batch):
    if run_batch.value:
        mo.md("*(batch runner — wire this to your full pair list + core.piv.run_pipeline per pair)*")
    else:
        mo.md("*batch not run yet — tuning above never triggers this*")
    return


if __name__ == "__main__":
    app.run()
