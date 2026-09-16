# AlphaIQ™ Build Environment Note

The repository historically contains an MT5-specific dependency that may not install on Linux CI. Existing AlphaIQ™ CI uses a platform-neutral requirements transformation rather than removing MT5 support from source. A successor should preserve that distinction: Linux research/service tests should not fail merely because a Windows/terminal-specific package is unavailable, while broker-specific adapter tests should run in an appropriate environment.
