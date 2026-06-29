# Modustry Indexer

Automatically indexes and compiles a list of Mindustry mods for Modustry and compatible mod browsers.

The indexer periodically scans public GitHub repositories and validates whether they can be safely included in the public mod list. Only repositories that match the required criteria are indexed.

## Criteria

To be included in the public index, a mod must meet all of the following requirements:

* Must have a valid `mod.json` or `mod.hjson` file.
* The mod metadata file must be located in the repository root or inside the `assets/` directory.
* Must use the `mindustry-mod` GitHub topic.
* Do **not** use `mindustry-mod-v6` or `mindustry-mod-v7`; these topics are ignored.
* Must have a `minGameVersion` greater than or equal to `136`.
* Must have a valid icon.

Repositories that do not match these requirements will be ignored by the indexer.

## Script Mod Compatibility

Compatibility with script-based mods is currently limited.

This limitation mainly exists because many script mods do not use GitHub releases. Because of that, the indexer may not be able to reliably detect version history, release dates, download counts, or other release-based metadata.

As a result, script mods may still be indexed, but they can be excluded from some filters, rankings, sorting options, or statistics that depend on release data.

## Opting Out

If you would like to remove your mod from the public browser, add the following field to your `mod.json` or `mod.hjson`:

```hjson
hideBrowser: true
```

Once detected, the mod will be ignored by the indexer and removed from the public list.

## Notes

The index is refreshed automatically from time to time. Changes to repository topics, metadata, icons, or opt-out settings may not appear immediately.
