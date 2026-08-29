Attribute VB_Name = "probe_claims"
Option Explicit
' ============================================================================
' Probe kit for the three EXPERIENCE-SETTLED claims in vba-excel-object-model
' (claudeBrain issue #43). Run on a THROWAWAY workbook in Excel's VBE: import
' this module (or paste it into a standard module) and run RunAllProbes (F5).
' All output goes to the Immediate window (Ctrl+G) — copy the whole block back
' into the issue verbatim.
'
' Discipline (claim-grounding skill): controls run FIRST. If either control
' fails, the harness is broken and NOTHING below it is evidence — stop the
' line, do not read the probe lines. Each probe prints exactly what happened,
' never a bare pass/fail, so the ledger row can quote the observation.
'
' AUTHORED WITHOUT A LIVE EXCEL HOST. The module deliberately uses only calls
' that are doc-settled elsewhere in the skill. If it fails to compile or run,
' that itself is a finding — report it on the issue.
' ============================================================================

Public Sub RunAllProbes()
    Debug.Print "=== vba-excel-object-model probes · " & _
                Format$(Now, "yyyy-mm-dd hh:nn") & " · Excel " & _
                Application.Version & " (" & Application.OperatingSystem & ") ==="
    If Not ControlsPass() Then
        Debug.Print "STOP-THE-LINE: a control failed. Nothing below this line is evidence."
        Exit Sub
    End If
    ProbeSpecialCellsNoMatch
    ProbePivotDataFieldRename
    ProbeUsedRangeAfterClear
    Debug.Print "=== done — paste this whole Immediate-window block into issue #43 ==="
End Sub

' ---------------------------------------------------------------------------
' Controls. POSITIVE: the API under test finds what is genuinely there.
' NEGATIVE: our error-capture pattern actually captures a raised error.
' ---------------------------------------------------------------------------
Private Function ControlsPass() As Boolean
    Dim ws As Worksheet, found As Range
    Dim positiveOk As Boolean, negativeOk As Boolean

    Set ws = ThisWorkbook.Worksheets.Add
    On Error GoTo Infra

    ws.Range("B2").Value2 = 42
    Set found = ws.Range("A1:C3").SpecialCells(xlCellTypeConstants)
    positiveOk = (found.Cells.Count = 1 And found.Address = "$B$2")
    Debug.Print "CONTROL positive (SpecialCells finds the one constant): " & _
                IIf(positiveOk, "PASS", "FAIL — got " & found.Address)

    On Error Resume Next
    Err.Raise 1004, , "control"
    negativeOk = (Err.Number = 1004)
    On Error GoTo Infra
    Debug.Print "CONTROL negative (raised 1004 is captured by the probe pattern): " & _
                IIf(negativeOk, "PASS", "FAIL")

    ControlsPass = positiveOk And negativeOk
    GoTo Clean
Infra:
    Debug.Print "CONTROL infrastructure error " & Err.Number & ": " & Err.Description
    ControlsPass = False
Clean:
    Application.DisplayAlerts = False
    ws.Delete
    Application.DisplayAlerts = True
End Function

' ---------------------------------------------------------------------------
' CLAIM 1 — "SpecialCells raises run-time 1004 ('No cells were found') when
' nothing matches, rather than returning Nothing or an empty range."
' ---------------------------------------------------------------------------
Private Sub ProbeSpecialCellsNoMatch()
    Dim ws As Worksheet, result As Range
    Dim errNum As Long, errDesc As String

    Set ws = ThisWorkbook.Worksheets.Add          ' fresh sheet: zero constants
    On Error Resume Next
    Set result = ws.Range("A1:C10").SpecialCells(xlCellTypeConstants)
    errNum = Err.Number: errDesc = Err.Description
    On Error GoTo 0

    If errNum = 1004 Then
        Debug.Print "PROBE specialcells-no-match: CONFIRMED — raised 1004 ('" & errDesc & "')"
    ElseIf errNum <> 0 Then
        Debug.Print "PROBE specialcells-no-match: UNEXPECTED — raised " & errNum & " ('" & errDesc & "'), not 1004"
    ElseIf result Is Nothing Then
        Debug.Print "PROBE specialcells-no-match: REFUTED — no error; returned Nothing"
    Else
        Debug.Print "PROBE specialcells-no-match: REFUTED — no error; returned " & _
                    result.Cells.Count & " cell(s) at " & result.Address
    End If

    Application.DisplayAlerts = False
    ws.Delete
    Application.DisplayAlerts = True
End Sub

' ---------------------------------------------------------------------------
' CLAIM 2 — "Renaming a PivotTable data field to the source field's own name
' raises an error." Includes its own negative control: a rename to a NON-
' colliding name must succeed, or the probe proves nothing about the collision.
' ---------------------------------------------------------------------------
Private Sub ProbePivotDataFieldRename()
    Dim wsData As Worksheet, wsPivot As Worksheet
    Dim cache As PivotCache, pivot As PivotTable, dataField As PivotField
    Dim errNum As Long, errDesc As String

    Set wsData = ThisWorkbook.Worksheets.Add
    wsData.Range("A1:B1").Value2 = Array("Region", "Amount")
    wsData.Range("A2:B2").Value2 = Array("East", 10)
    wsData.Range("A3:B3").Value2 = Array("West", 20)

    Set wsPivot = ThisWorkbook.Worksheets.Add
    On Error GoTo Infra
    ' SourceData as a STRING, per the skill's own doc-settled rule.
    Set cache = ThisWorkbook.PivotCaches.Create( _
                    SourceType:=xlDatabase, _
                    SourceData:="'" & wsData.Name & "'!R1C1:R3C2")
    Set pivot = cache.CreatePivotTable( _
                    TableDestination:=wsPivot.Range("A3"), TableName:="ptProbe")
    pivot.PivotFields("Region").Orientation = xlRowField
    pivot.PivotFields("Amount").Orientation = xlDataField
    Set dataField = pivot.DataFields(1)
    Debug.Print "  (pivot built; data field default name: '" & dataField.Name & "')"

    ' Negative control: a non-colliding rename must succeed.
    On Error Resume Next
    dataField.Name = "Amount Probe Total"
    errNum = Err.Number: errDesc = Err.Description
    On Error GoTo Infra
    If errNum <> 0 Then
        Debug.Print "PROBE pivot-rename: STOP — even the non-colliding rename raised " & _
                    errNum & " ('" & errDesc & "'); the collision result below would be meaningless."
        GoTo Clean
    End If
    Debug.Print "  (negative control: rename to 'Amount Probe Total' succeeded)"

    ' The collision under test.
    On Error Resume Next
    dataField.Name = "Amount"
    errNum = Err.Number: errDesc = Err.Description
    On Error GoTo Infra
    If errNum <> 0 Then
        Debug.Print "PROBE pivot-rename: CONFIRMED — rename to source name 'Amount' raised " & _
                    errNum & " ('" & errDesc & "')"
    Else
        Debug.Print "PROBE pivot-rename: REFUTED — rename to source name 'Amount' succeeded; " & _
                    "field is now '" & dataField.Name & "'"
    End If
    GoTo Clean
Infra:
    Debug.Print "PROBE pivot-rename: INFRASTRUCTURE error " & Err.Number & " ('" & _
                Err.Description & "') while building the pivot — not evidence either way."
Clean:
    Application.DisplayAlerts = False
    wsPivot.Delete
    wsData.Delete
    Application.DisplayAlerts = True
End Sub

' ---------------------------------------------------------------------------
' CLAIM 3 — "UsedRange over-reports: it does not reliably shrink after cells
' are cleared." Records the observed address at each step; both outcomes are
' informative, and the in-session result may differ from the after-save one —
' the optional second stage covers that.
' ---------------------------------------------------------------------------
Private Sub ProbeUsedRangeAfterClear()
    Dim ws As Worksheet
    Dim beforeClear As String, afterClear As String

    Set ws = ThisWorkbook.Worksheets.Add
    ws.Range("A1:J50").Value2 = 1
    beforeClear = ws.UsedRange.Address

    ws.Range("A11:J50").Clear
    afterClear = ws.UsedRange.Address

    Debug.Print "PROBE usedrange-after-clear: filled A1:J50 (UsedRange=" & beforeClear & _
                "), cleared A11:J50, UsedRange now " & afterClear
    If afterClear = beforeClear Then
        Debug.Print "  → CONFIRMED (in-session): UsedRange did not shrink after Clear"
    ElseIf afterClear = "$A$1:$J$10" Then
        Debug.Print "  → REFUTED (in-session): UsedRange shrank to the live data immediately"
    Else
        Debug.Print "  → PARTIAL: shrank, but not to the live extent — record the address above"
    End If
    Debug.Print "  Optional stage 2: save the workbook, reopen it, and print " & _
                "ws.UsedRange.Address again — the claim is about reliability across " & _
                "that boundary too. Record both results in the issue."

    Application.DisplayAlerts = False
    ws.Delete
    Application.DisplayAlerts = True
End Sub
