import React, { useState, useEffect } from 'react';
import { DataGrid } from '@mui/x-data-grid';
import { Button, Modal, Box, TextField, MenuItem, IconButton } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';

const modalStyle = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: 400,
    bgcolor: 'background.paper',
    boxShadow: 24,
    p: 4,
    borderRadius: 2
};

const ManageCategories = () => {
    const [categories, setCategories] = useState([]);
    const [openModal, setOpenModal] = useState(false);
    const [editCategory, setEditCategory] = useState(null);
    const userId = localStorage.getItem('user_id');

    // Fetch categories
    const fetchCategories = async () => {
        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`http://localhost:8000/subcategories/${userId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            if (!response.ok) throw new Error('Failed to fetch categories');
            const data = await response.json();
            setCategories(data);
        } catch (error) {
            console.error('Fetch error:', error);
        }
    };

    // Handle edit submission
    const handleEditSubmit = async () => {
        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`http://localhost:8000/subcategories/${userId}/${editCategory.subcategory_id}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    category: editCategory.category,
                    subcategory_name: editCategory.subcategory_name
                })
            });

            if (!response.ok) throw new Error('Failed to update category');
            
            await fetchCategories(); // Refresh the list
            setOpenModal(false);
        } catch (error) {
            console.error('Update error:', error);
        }
    };

    const columns = [
        { field: 'category', headerName: 'Category', width: 130 },
        { field: 'subcategory_name', headerName: 'Subcategory', width: 130 },
        { field: 'is_standard', headerName: 'Standard', width: 100 },
        {
            field: 'actions',
            headerName: 'Actions',
            width: 100,
            renderCell: (params) => (
                <IconButton 
                    onClick={() => {
                        if (!params.row.is_standard) {
                            setEditCategory(params.row);
                            setOpenModal(true);
                        }
                    }}
                    disabled={params.row.is_standard}
                >
                    <EditIcon />
                </IconButton>
            )
        }
    ];

    useEffect(() => {
        fetchCategories();
    }, []);

    return (
        <div style={{ height: 400, width: '100%' }}>
            <DataGrid
                rows={categories}
                columns={columns}
                pageSize={5}
                rowsPerPageOptions={[5]}
                getRowId={(row) => row.subcategory_id}
            />

            <Modal
                open={openModal}
                onClose={() => setOpenModal(false)}
            >
                <Box sx={modalStyle}>
                    <h2>Edit Category</h2>
                    {editCategory && (
                        <>
                            <TextField
                                fullWidth
                                label="Category"
                                value={editCategory.category}
                                onChange={(e) => setEditCategory({
                                    ...editCategory,
                                    category: e.target.value
                                })}
                                margin="normal"
                            />
                            <TextField
                                fullWidth
                                label="Subcategory"
                                value={editCategory.subcategory_name}
                                onChange={(e) => setEditCategory({
                                    ...editCategory,
                                    subcategory_name: e.target.value
                                })}
                                margin="normal"
                            />
                            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
                                <Button onClick={() => setOpenModal(false)}>Cancel</Button>
                                <Button variant="contained" onClick={handleEditSubmit}>Save</Button>
                            </Box>
                        </>
                    )}
                </Box>
            </Modal>
        </div>
    );
};

export default ManageCategories; 