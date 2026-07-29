# Storage readiness report 1.0.0

The marker-validated Seagate data root exists and contains every required NaS
directory. The non-mutating preflight reports 4,587,132,846,080 available bytes,
well above the declared 1 GiB acquisition minimum.

Readiness is nevertheless **blocked**: macOS reports the filesystem mount as
read-only and denies write access. The check performed no write probe, downloaded
no source artifact, and accessed no biomedical data.

Official NCBI headers separately establish the proposed GSE81538 processed
artifact name, content type, last-modified time, and exact size of 54,838,076
bytes. Its SHA-256 remains pending because the system correctly refused to
download molecular bytes without writable governed storage.

Next action: remount or repair `/Volumes/AGNDJ 6TB` read-write, rerun the
preflight, and only then execute a checksum-verifying immutable download into
the proposed object-store key.
