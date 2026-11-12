property seenVolumes : {}
property lastError : missing value

on run
    set seenVolumes to {}
    startIngest()
end run

on startIngest()
    set lastError to missing value
    try
        do shell script launcherCommand
    on error errorMessage
        display alert "Field Lab" message errorMessage as critical
        quit
    end try
end startIngest

on reopen
    startIngest()
end reopen

on idle
    try
        set helperPath to POSIX path of (path to resource "ingest_cards.py")
        set helperCommand to pythonCommand & space & quoted form of helperPath & space & quoted form of applicationHome
        set mountedVolumes to paragraphs of (do shell script helperCommand & " list" without altering line endings)
        set newVolumes to {}
        set labels to {}
        repeat with mountPath in mountedVolumes
            set mountPath to contents of mountPath
            if mountPath is not "" and mountPath is not in seenVolumes then
                set end of newVolumes to mountPath
                set end of labels to text 1 thru ((offset of tab in mountPath) - 1) of mountPath
            end if
        end repeat
        set seenVolumes to mountedVolumes
        if newVolumes is not {} then
            activate
            set selectedVolumes to choose from list labels with title "Field Lab Ingest" with prompt "Choose cards to use as sources" OK button name "Set Sources" cancel button name "Skip" with multiple selections allowed
            if selectedVolumes is not false then
                set addCommand to helperCommand & " add"
                repeat with cardIndex from 1 to count labels
                    if item cardIndex of labels is in selectedVolumes then
                        set addCommand to addCommand & space & quoted form of (item cardIndex of newVolumes)
                    end if
                end repeat
                set unavailable to do shell script addCommand
                if unavailable is not "" then display alert "Some cards were skipped" message ("These volumes are no longer eligible:" & return & unavailable)
            end if
        end if
        set lastError to missing value
    on error errorMessage
        if errorMessage is not lastError then
            set lastError to errorMessage
            activate
            display alert "Field Lab Ingest" message errorMessage as warning
        end if
        return 15
    end try
    return 3
end idle
