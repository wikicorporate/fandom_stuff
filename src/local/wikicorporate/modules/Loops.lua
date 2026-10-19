-- <nowiki>
--------------------------------------------------------------------------------
-- Lua module implementing features similar to [[mw:Extension:Loops]].
--
-- @module lööps
-- @alias  loops
-- @author [[User:ExE Boss]]
-- @require [[Global Lua Modules/TableTools|Dev:TableTools]]
--------------------------------------------------------------------------------

local libraryUtil = require("libraryUtil")
local tableTools  = require("Dev:TableTools")

local checkType = libraryUtil.checkType
local checkTypeForNamedArg = libraryUtil.checkTypeForNamedArg

local ustring = mw.ustring
local loops = {}

local function escapePattern(pattern)
    return ustring.gsub(pattern, "([%(%)%.%%%+%-%*%?%[%^%$%]])", "%%%1")
end

local function isFrame(frame)
    return type(frame) == "table"
        and type(frame.args) == "table"
        and type(frame.getParent) == "function"
end

local function preprocess(frame, msg)
    msg = ustring.gsub(msg, "«", "<")
    msg = ustring.gsub(msg, "»", ">")
    msg = ustring.gsub(msg, "¦", "|")
    msg = ustring.gsub(msg, "²{", "{{")
    msg = ustring.gsub(msg, "}²", "}}")
    return frame:preprocess(msg)
end
loops._preprocess = preprocess

function loops.numArgs(frame)
    checkType("numArgs", 1, frame, "table")
    local args
    if isFrame(frame) then
        args = (frame:getParent() or frame).args
    else
        args = frame
    end
    return tableTools.length(args)
end

function loops.forNumArgs(frame)
    local frameArgs, parentArgs
    checkType("forNumArgs", 1, frame, "table")
    if isFrame(frame) then
        frameArgs  = frame.args
        parentArgs = frame:getParent().args
    else
        return error("forNumArgs only supports invocation")
    end

    local kPattern, vPattern, template
    local frameNumArgs = tableTools.length(frameArgs)
    if frameNumArgs >= 3 then
        kPattern = frameArgs[1]
        vPattern = frameArgs[2]
        template = frameArgs[3]
    elseif frameNumArgs >= 2 then
        vPattern = frameArgs[1]
        template = frameArgs[2]
    else
        template = frameArgs[1]
    end

    kPattern = frameArgs.key      or kPattern
    vPattern = frameArgs.value    or vPattern
    template = frameArgs.template or template

    checkTypeForNamedArg("forNumArgs", "key",      kPattern, "string", true)
    checkTypeForNamedArg("forNumArgs", "value",    vPattern, "string", true)
    checkTypeForNamedArg("forNumArgs", "template", template, "string", true)

    if template == nil then
        return error("Must supply template parameter to forNumArgs")
    end

    vPattern = vPattern or "$1"
    if kPattern ~= nil then
        if #kPattern > 0 then
            if kPattern == vPattern then
                return error("key pattern must be different from value pattern")
            end
            kPattern = escapePattern(kPattern)
        else
            kPattern = nil
        end
    elseif vPattern ~= "$2" then
        kPattern = "%$2"
    end
    if #vPattern == 0 then
        vPattern = nil
    else
        vPattern = escapePattern(vPattern)
    end

    local result = {}
    for k = 1, tableTools.length(parentArgs) do
        local v = parentArgs[k]
        if v ~= nil then
            local msg = template
            if kPattern then
                msg = ustring.gsub(msg, kPattern, function() return tostring(k) end)
            end
            if vPattern then
                msg = ustring.gsub(msg, vPattern, function() return tostring(v) end)
            end
            result[#result + 1] = preprocess(frame, msg)
        end
    end

    return table.concat(result)
end

function loops.loop(frame)
    checkType("loop", 1, frame, "table")
    if not isFrame(frame) then
        return error("loop only supports invocation")
    end

    local args = frame.args[1] and frame.args or (frame:getParent() or frame).args
    local rawPattern = args[1] or "$1"
    local escapedPattern = escapePattern(rawPattern)

    local start = tonumber(args[2]) or 1
    local loopsPerformed = tonumber(args[3]) or 0
    local template = args[4] or ""

    if loopsPerformed == 0 or template == "" then
        return ""
    end

    local fin = loopsPerformed < 0 and start + (loopsPerformed + 1) or (start - 1) + loopsPerformed
    local step = loopsPerformed < 0 and -1 or 1

    local result = {}
    for i = start, fin, step do
        result[#result + 1] = ustring.gsub(template, escapedPattern, function() return tostring(i) end)
    end

    return preprocess(frame, table.concat(result))
end

return loops
