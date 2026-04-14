# OneDrive — Full Command Reference

Script: `{baseDir}/scripts/ms_graph.py`

## List files
```bash
python3 {baseDir}/scripts/ms_graph.py onedrive list [--path "/"] [--top 20]
```

## Get file/folder info
```bash
python3 {baseDir}/scripts/ms_graph.py onedrive info --item-id <id>
```

## Download file
```bash
python3 {baseDir}/scripts/ms_graph.py onedrive download \
  --item-id <id> [--output /path/to/save]
```

## Upload file
```bash
python3 {baseDir}/scripts/ms_graph.py onedrive upload \
  --local-file /path/to/file \
  --remote-path "/folder/filename.ext"
```

## Create folder
```bash
python3 {baseDir}/scripts/ms_graph.py onedrive mkdir \
  --name "New Folder" [--parent-id <id>]
```

## Delete file/folder
```bash
python3 {baseDir}/scripts/ms_graph.py onedrive delete --item-id <id>
```

## Search files
```bash
python3 {baseDir}/scripts/ms_graph.py onedrive search --query "keyword"
```

## Notes

- `--path` defaults to root `/`; use paths like `/Documents` or `/Work/Reports`
- `--output` for download defaults to current directory using the original filename
- `--remote-path` for upload must include the filename (e.g. `/Documents/report.pdf`)
- `--parent-id` for mkdir: omit to create folder in root
- Delete is permanent — OneDrive recycle bin may retain it for 30 days
