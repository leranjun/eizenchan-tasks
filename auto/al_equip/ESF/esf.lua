--[[
    Azure Lane: Equipment Stats Formatter V20210729
    Made with ♥ by User:Leranjun
]]
package.path =
    package.path ..
    -- ";/data/project/eizenchan/al-equip/ESF/?.lua;C:/Users/Admin/Downloads/data/project/eizenchan/al-equip/ESF/?.lua"
    ";/data/project/eizenchan/al-equip/ESF/?.lua"

-- Define global for linter
slot0 = slot0 or {}
pg = pg or {}
unpack = unpack or table.unpack

-- Config list
local esf = {}
esf.version = "20210729"

function tprint(t, ind)
    ind = ind or 0
    local isouter = (ind == 0)

    local r = ""
    if (isouter) then
        r = "{\n"
    else
        r = "{ "
    end

    for k, v in pairs(t) do
        if (isouter) then
            r = r .. string.rep(" ", ind + 4)
        end

        if (type(k) == "number") then
            r = r .. "[" .. k .. "] = "
        elseif (type(k) == "string") then
            r = r .. '["' .. k .. '"] = '
        end

        if (type(v) == "number") then
            r = r .. v .. ", "
        elseif (type(v) == "string") then
            r = r .. '"' .. v .. '"' .. ", "
        elseif (type(v) == "table") then
            r = r .. tprint(v, ind + 4)
        end
    end

    if (isouter) then
        r = r .. string.rep(" ", ind)
    end
    r = r .. "}"
    if (ind == 4) then
        r = r .. ",\n"
    end

    r = r:gsub(", }", " }"):gsub("},\n}", "}\n}")

    return r
end

-- Validate if name is in blacklist
function validateName(name)
    if (not name) then
        -- Name is nil
        return false
    end

    for _, v in pairs(esf.blacklist) do
        if (string.find(name, v)) then
            return false
        end
    end

    return true
end

-- Add nationality
function addNat(name, nat)
    for _, v in pairs(esf.nationalities) do
        if (name == v) then
            name = name .. "（" .. esf.NAT[(nat or 0)] .. "）"
        end
    end
    return name
end

-- Main function
-- print("Azure Lane: Equipment Stats Formatter V" .. esf.version)

-- Require equip data
require("dat.equip_data_statistics")
esf.data = slot0.equip_data_statistics
setmetatable(esf.data, nil)

-- Require configs
esf.blacklist = require("src.esf_blacklist")
esf.nationalities = require("src.esf_nationality")
esf.links = require("src.esf_links")

-- Constant
esf.NAT = {
    [0] = "未知",
    [1] = "白鹰",
    [2] = "皇家",
    [3] = "重樱",
    [4] = "铁血",
    [5] = "东煌",
    [6] = "撒丁",
    [7] = "北联",
    [8] = "鸢尾"
}

-- Initialise output and sort table
esf.output = {}
esf.sort = { {}, {} }
esf.keep = {}

for _, v in pairs(esf.data.subList) do
    -- require("dat." .. esf.data.subFolderName:lower() .. "." .. v)
    require("dat." .. v)
end

for _, cur in pairs(pg) do
    for _, v in pairs(cur) do
        if (validateName(v.name)) then
            -- Change half-width punctuation to full-width
            name = addNat(string.gsub(string.gsub(v.name, "%(", "（"), "%)", "）"), v.nationality)
            -- Add to output table
            esf.output[name] = esf.output[name] or {}
            -- esf.output[name]["type"] = v.type
            esf.output[name][v.tech] = v.rarity
            esf.output[name].link = esf.links[name]
            esf.keep[name] = math.max(v.id, (esf.keep[name] or 0))
            table.insert(esf.sort[1], { v.id, name })
        end
    end
end

for _, v in pairs(esf.output) do
    table.sort(v)
end

table.sort(
    esf.sort[1],
    function(lhs, rhs)
        return lhs[1] < rhs[1]
    end
)

esf.outstr = "return {\n"
for _, v in pairs(esf.sort[1]) do
    id, name = unpack(v)
    if (esf.keep[name] == id) then
        esf.outstr = esf.outstr .. '    ["' .. name .. '"] = { '
        esf.sort[2] = {}
        for k, _ in pairs(esf.output[name]) do
            table.insert(esf.sort[2], k)
        end
        table.sort(
            esf.sort[2],
            function(lhs, rhs)
                if (tonumber(lhs) and tonumber(rhs)) then
                    return tonumber(lhs) < tonumber(rhs)
                else
                    return false
                end
            end
        )
        for _, k in pairs(esf.sort[2]) do
            esf.outstr = esf.outstr .. "["
            if (type(k) == "number") then
                esf.outstr = esf.outstr .. k
            elseif (type(k) == "string") then
                esf.outstr = esf.outstr .. "\"" .. k .. "\""
            end
            esf.outstr = esf.outstr .. "] = "
            if (type(k) == "number") then
                esf.outstr = esf.outstr .. esf.output[name][k]
            elseif (type(k) == "string") then
                esf.outstr = esf.outstr .. "\"" .. esf.output[name][k] .. "\""
            end
            esf.outstr = esf.outstr .. ", "
        end
        esf.outstr = esf.outstr .. "},\n"
    end
end
esf.outstr = esf.outstr .. "}"
esf.outstr = esf.outstr:gsub(", }", " }"):gsub("},\n}", "}\n}")

-- Open and write to file
io.open("equip_formatted.lua", "w+"):write(esf.outstr)

-- print("Output successfully stored in file equip_formatted.lua.")

-- os.execute("pause")
