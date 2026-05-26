import TextField from "@mui/material/TextField";
import InputAdornment from "@mui/material/InputAdornment";
import Autocomplete, { autocompleteClasses } from "@mui/material/Autocomplete";
import { Iconify } from "@admin/components/iconify";
function PostSearch({ posts, sx }) {
  return <Autocomplete
    sx={{ width: 280 }}
    autoHighlight
    popupIcon={null}
    slotProps={{
      paper: {
        sx: {
          width: 320,
          [`& .${autocompleteClasses.option}`]: {
            typography: "body2"
          },
          ...sx
        }
      }
    }}
    options={posts}
    getOptionLabel={(post) => post.title}
    isOptionEqualToValue={(option, value) => option.id === value.id}
    renderInput={(params) => <TextField
      {...params}
      placeholder="Search post..."
      slotProps={{
        input: {
          ...params.InputProps,
          startAdornment: <InputAdornment position="start">
                  <Iconify
            icon="eva:search-fill"
            sx={{ ml: 1, width: 20, height: 20, color: "text.disabled" }}
          />
                </InputAdornment>
        }
      }}
    />}
  />;
}
export {
  PostSearch
};
