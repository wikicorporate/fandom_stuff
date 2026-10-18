-- <nowiki>
--------------------------------------------------------------------------------
-- Lua module implementing features similar to [[mw:Extension:Loops]].
--
-- @module lööps
-- @alias  loops
-- @author [[User:ExE Boss]]
-- @require [[Global Lua Modules/TableTools|Dev:TableTools]]
--------------------------------------------------------------------------------

local libraryUtil = require("libraryUtil");
local tableTools  = require("Dev:TableTools");

local checkType = libraryUtil.checkType;
local checkTypeForNamedArg = libraryUtil.checkTypeForNamedArg;

local ustring = mw.ustring;
local loops = {};

local function escapePattern(pattern)
	return ustring.gsub(pattern, "([%(%)%.%%%+%-%*%?%[%^%$%]])", "%%%1")
end

local function isFrame(frame)
	return type(frame) == "table"
		and type(frame.args) == "table"
		and type(frame.getParent) == "function";
end

--------------------------------------------------------------------------------
-- Preprocesses text escaped using the [[mw:Extension:DynamicPageList3]] method.
--
-- @function loops._preprocess
-- @param {Frame} frame
-- @param {string} msg
-- @return {string}
--------------------------------------------------------------------------------
local function preprocess(frame, msg)
	msg = ustring.gsub(msg, "«", "<");
	msg = ustring.gsub(msg, "»", ">");
	msg = ustring.gsub(msg, "¦", "|");
	msg = ustring.gsub(msg, "²{", "{{");
	msg = ustring.gsub(msg, "}²", "}}");
	return frame:preprocess(msg);
end
loops._preprocess = preprocess;

--------------------------------------------------------------------------------
-- @param {Frame|table} args
-- @return {number}
-- @usage {{#invoke:Loops|numArgs}}
--------------------------------------------------------------------------------
function loops.numArgs(frame)
	checkType("numArgs", 1, frame, "table");
	local args;
	if (isFrame(frame)) then
		args = (frame:getParent() or frame).args;
	else
		args = frame;
	end
	return tableTools.length(args);
end

--------------------------------------------------------------------------------
-- @param {Frame} args
-- @return {string}
--
-- @usage {{#invoke:Loops|forNumArgs|template string}}
-- @usage {{#invoke:Loops|forNumArgs|value pattern|template string}}
-- @usage {{#invoke:Loops|forNumArgs|key pattern|value pattern|template string}}
-- @usage
--  {{#invoke:Loops|forNumArgs
--  | template = template string
--  }}
-- @usage
--  {{#invoke:Loops|forNumArgs
--  | value    = value pattern
--  | template = template string
--  }}
-- @usage
--  {{#invoke:Loops|forNumArgs
--  | key      = key pattern
--  | template = template string
--  }}
-- @usage
--  {{#invoke:Loops|forNumArgs
--  | key      = key pattern
--  | value    = value pattern
--  | template = template string
--  }}
--------------------------------------------------------------------------------
function loops.forNumArgs(frame)
	local frameArgs, parentArgs;
	checkType("numArgs", 1, frame, "table");
	if (isFrame(frame)) then
		frameArgs  = frame.args;
		parentArgs = frame:getParent().args;
	else
		return error("forNumArgs only supports invocation");
	end

	local kPattern, vPattern, template;
	local frameNumArgs = tableTools.length(frameArgs);
	if (frameNumArgs >= 3) then
		kPattern = frameArgs[1];
		vPattern = frameArgs[2];
		template = frameArgs[3];
	elseif (frameNumArgs >= 2) then
		vPattern = frameArgs[1];
		template = frameArgs[2];
	else
		template = frameArgs[1];
	end

	kPattern = frameArgs.key      or kPattern;
	vPattern = frameArgs.value    or vPattern;
	template = frameArgs.template or template;

	checkTypeForNamedArg("forNumArgs", "key",      kPattern, "string", true);
	checkTypeForNamedArg("forNumArgs", "value",    vPattern, "string", true);
	checkTypeForNamedArg("forNumArgs", "template", template, "string", true);

	if (template == nil) then
		return error("Must supply template parameter to forNumArgs");
	end

	vPattern = vPattern or "$1";
	if (kPattern ~= nil) then
		if (#kPattern > 0) then
			if (kPattern == vPattern) then
				return error("key pattern must be different from value pattern");
			end
			kPattern = escapePattern(kPattern);
		else
			kPattern = nil;
		end
	elseif (vPattern ~= "$2") then
		kPattern = "%$2";
	end
	if (#vPattern == 0) then
		vPattern = nil;
	else
		vPattern = escapePattern(vPattern);
	end

	local result = {};
	local v, msg;
	for k = 1, tableTools.length(parentArgs) do
		v = parentArgs[k];
		if (v ~= nil) then
			msg = template;
			if (kPattern) then
				msg = ustring.gsub(msg, kPattern, (ustring.gsub(tostring(k), "%%", "%%%%")));
			end
			if (vPattern) then
				msg = ustring.gsub(msg, vPattern, (ustring.gsub(tostring(v), "%%", "%%%%")));
			end
			result[#result + 1] = preprocess(frame, msg);
		end
	end

	return table.concat(result);
end

--------------------------------------------------------------------------------
-- Parses and prints wikitext markup N times
--
-- @param {Frame} args
-- @param[opt] {string} args[1] Pattern. `$1` by default
-- @param {number} args[2] Starting value
-- @param {number} args[3] Number loops to be performed
-- @param {string} args[4] Wikitext markup
-- @return {string}
--------------------------------------------------------------------------------
function loops.loop(frame)
	local frameArgs
	checkType("numArgs", 1, frame, "table")
	if (isFrame(frame)) then
		frameArgs = (frame:getParent() or frame).args
	else
		return error("loop only supports invocation")
	end
	
	local pattern = frame.args[1] or "$1"
	
	local start = tonumber(frame.args[2])
	local loopsPerformed = tonumber(frame.args[3])
	-- {{#loop}} supports negative values for loopsPerformed
	local fin = loopsPerformed < 0 and start + (loopsPerformed + 1) or (start - 1) + loopsPerformed
	local step = loopsPerformed < 0 and -1 or 1
	
	local template = frame.args[4]
	
	local result = {}
	local msg
	for i = start, fin, step do
		msg = ustring.gsub(template, pattern, i)
		result[#result + 1] = msg
	end
	
	return preprocess(frame, table.concat(result)) -- preprocess at the end
end

return loops;
